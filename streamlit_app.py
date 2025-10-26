import requests
#from bs4 import BeautifulSoup
import streamlit as st
import pandas as pd
import time
import re
from io import BytesIO

# --- Função auxiliar para extrair atributos de imagem ---
def extrair_url_imagem(img_tag):
    if not img_tag:
        return ""
    # tenta vários atributos comuns de lazy-loading / srcset
    for attr in ("data-src", "data-original", "data-lazy", "data-srcset", "data-imgsrc", "src"):
        if img_tag.has_attr(attr):
            val = img_tag.get(attr)
            if not val:
                continue
            # se for srcset, pega a primeira URL antes do espaço
            if attr == "data-srcset" or "srcset" in attr:
                # srcset tem formato "url 1x, url2 2x" -> pega a primeira URL
                return val.split(",")[0].split()[0]
            return val
    # fallback para alt contendo uma URL rara
    return ""

# --- Função auxiliar para extrair título com vários fallbacks ---
def extrair_titulo(item, link_tag, img_tag):
    # 1) atributo title do link
    if link_tag and link_tag.has_attr("title") and link_tag.get("title").strip():
        return link_tag.get("title").strip()
    # 2) tags h2/h3 conhecidas
    for tag_name in ("h2", "h3"):
        tag = item.find(tag_name)
        if tag and tag.get_text().strip():
            return tag.get_text().strip()
    # 3) atributo alt da imagem
    if img_tag and img_tag.has_attr("alt") and img_tag.get("alt").strip():
        return img_tag.get("alt").strip()
    # 4) atributo aria-label
    if item.has_attr("aria-label") and item.get("aria-label").strip():
        return item.get("aria-label").strip()
    # fallback
    return "Sem título"

# --- Função auxiliar para extrair preço com vários fallbacks ---
def extrair_preco(item):
    # Tenta classes diferentes
    # 1) andes-money-amount__fraction (ML atual)
    frac = item.find("span", class_=re.compile("(andes-money-amount__fraction|price-tag-fraction|ui-search-price__part--integer)"))
    cents = item.find("span", class_=re.compile("(andes-money-amount__cents|price-tag-cents|ui-search-price__part--decimal)"))
    if frac:
        price = frac.get_text().strip()
        if cents:
            price += "," + cents.get_text().strip()
        # remove pontos de milhar
        price = price.replace(".", "")
        return price
    # 2) procura por qualquer padrão numérico dentro de tags de preço
    text = item.get_text(separator=" ")
    m = re.search(r"R\$\s*([\d\.\,]+)", text)
    if m:
        return m.group(1).replace(".", "")
    # 3) fallback: vazio
    return "Preço não encontrado"

# --- Função para buscar produtos (robusta) ---
def buscar_produtos(produto, paginas, delay=1.0):
    cabecalho = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/141.0.0.0 Safari/537.36'
        ),
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8"
    }

    base_url = f"https://lista.mercadolivre.com.br/{produto}"
    produtos = []
    vistos = set()

    for pagina in range(1, paginas + 1):
        url = f"{base_url}_Desde_{(pagina - 1) * 50 + 1}"
        try:
            r = requests.get(url, headers=cabecalho, timeout=15)
        except Exception as e:
            st.warning(f"Erro ao conectar à página {pagina}: {e}")
            continue

        if r.status_code != 200:
            st.warning(f"⚠️ Erro ao acessar página {pagina}: {r.status_code}")
            continue

        site = BeautifulSoup(r.text, "html.parser")

        # Busca os itens da lista — vários sites usam <li class="ui-search-layout__item">
        itens = site.find_all("li", class_=re.compile("ui-search-layout__item|results-item|ui-search-result"))

        if not itens:
            # fallback: procurar por blocos <div> de resultado
            itens = site.find_all("div", class_=re.compile("ui-search-result|ui-search-result__wrapper"))

        if not itens:
            st.info("Nenhum item encontrado nesta página (estrutura pode ter mudado).")
            break

        for item in itens:
            # pegar link principal
            link_tag = item.find("a", href=True)
            link = link_tag["href"] if link_tag else ""

            # extrair imagem e título com muitos fallbacks
            img_tag = item.find("img")
            imagem = extrair_url_imagem(img_tag)

            titulo = extrair_titulo(item, link_tag, img_tag)
            # evita repetir produtos por título+link
            chave = (titulo, link)
            if chave in vistos:
                continue
            vistos.add(chave)

            preco = extrair_preco(item)

            produtos.append({
                "Imagem": imagem,
                "Produto": titulo,
                "Preço (R$)": preco,
                "Link": link
            })

        time.sleep(delay)

    return produtos

# --- Interface Streamlit ---
st.set_page_config(page_title="Busca Mercado Livre", layout="wide")
st.title("🛒 Busca de Produtos no Mercado Livre (robusto)")

with st.sidebar:
    st.header("Configurações")
    produto = st.text_input("🔍 Produto para buscar", "Xiaomi")
    paginas = st.slider("📄 Quantas páginas buscar", 1, 6, 3)
    delay = st.number_input("⏱ Delay entre páginas (s)", min_value=0.0, max_value=5.0, value=1.0, step=0.1)
    st.write("---")
    st.write("Observação: o Mercado Livre pode mudar a estrutura do HTML. Este app tenta vários fallbacks para imagens/títulos/preços.")

if st.button("Buscar"):
    with st.spinner("Buscando produtos... aguarde"):
        resultados = buscar_produtos(produto, paginas, delay=delay)

    if not resultados:
        st.warning("Nenhum produto encontrado. Tente outro termo ou aumente páginas.")
    else:
        df = pd.DataFrame(resultados)
        st.success(f"✅ {len(df)} produtos encontrados.")

        # Botão para exportar CSV
        csv_bytes = df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Exportar CSV", data=csv_bytes, file_name=f"ml_{produto}.csv", mime="text/csv")

        # Mostrar produtos em cards (duas colunas por linha)
        cols = st.columns(2)
        for idx, row in df.iterrows():
            col = cols[idx % 2]
            with col:
                # Imagem
                if row["Imagem"]:
                    try:
                        st.image(row["Imagem"], width=150)
                    except Exception:
                        # imagem inválida: mostrar texto
                        st.write("🖼️ (imagem indisponível)")
                else:
                    st.write("🖼️ (Sem imagem)")

                # Título e preço
                st.markdown(f"**{row['Produto']}**")
                st.write(f"💰 R$ {row['Preço (R$)']}")

                # Link que abre em nova aba
                if row["Link"]:
                    # usamos HTML para target="_blank"
                    st.markdown(f'<a href="{row["Link"]}" target="_blank" rel="noopener">🔗 Abrir Produto</a>', unsafe_allow_html=True)
                st.markdown("---")

