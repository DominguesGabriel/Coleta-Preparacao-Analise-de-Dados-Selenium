import json
import re
import time
from dataclasses import dataclass
from typing import List, Optional, TypedDict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

class AtorInfo(TypedDict):
    nome: str
    personagem: str
    episodios: Optional[int] #

@dataclass
class Serie:
    titulo: str
    anoEstreia: int
    anoEncerramento: Optional[int]
    numeroEpisodios: Optional[int]
    classificacao: Optional[str]
    link: str
    nota: float
    elenco: List[AtorInfo]
    popularidade: Optional[int]

def extrair_anos(periodo_str):
    # Garante que estamos lidando com um hífen normal para facilitar
    partes = periodo_str.strip().replace("–", "-").split('-')
    
    anoEstreia = None
    anoEncerramento = None
    
    # Pega o ano de estreia (primeira parte)
    if partes and partes[0]:
        anoEstreia = int(partes[0])
        
    # Verifica se existe uma segunda parte e se ela contém um ano
    if len(partes) > 1 and partes[1]:
        anoEncerramento = int(partes[1])

    return anoEstreia, anoEncerramento

def buscar_informacoes_adicionais(link):
    try:
        driver.get(link)
        popularidade = int(driver.find_element(By.CSS_SELECTOR, '[data-testid="hero-rating-bar__popularity__score"]').text.replace(".", ""))

        elenco = []
        elenco_section = driver.find_element(By.XPATH, r'//*[@id="__next"]/main/div/section[1]/div/section/div/div[1]/section[5]')
        ator_tags = elenco_section.find_elements(By.CSS_SELECTOR, '[data-testid="title-cast-item"]')
        for ator in ator_tags:
            nome = ator.find_element(By.CSS_SELECTOR, '[data-testid="title-cast-item__actor"]').text
            personagem = ator.find_element(By.CSS_SELECTOR, '[data-testid="cast-item-characters-link"] span').text
            episodios = int(ator.find_element(By.CSS_SELECTOR, '[data-testid="title-cast-item__eps-toggle__large"]').text.split(" ")[0])
            elenco.append({"ator/atriz": nome, "personagem": personagem, "episodios": episodios})

        print(f"✅ Dados adicionais de '{link}' coletados com sucesso.")
        print(f"Elenco: {elenco}, Popularidade: {popularidade}")

        return elenco, popularidade 
    except Exception as e:
        print(f"Problema ao tentar ler dados adicionais de uma série: {e}")
        return None, None
    
def cria_serie(imdb_li_tag):
    try:
        titulo = imdb_li_tag.find_element(By.CLASS_NAME, "ipc-title__text").text
        titulo_limpo = re.sub(r'^\d+\.\s*', "", titulo)
        metadados_spans = imdb_li_tag.find_elements(By.CSS_SELECTOR, "span.cli-title-metadata-item")

        anoEstreia, anoEncerramento = None, None
        numeroEpisodios = None
        classificacao = None

        if len(metadados_spans) > 0:
            periodo = metadados_spans[0].text
            anoEstreia, anoEncerramento = extrair_anos(periodo)

        if len(metadados_spans) > 1:
            try:
                numeroEpisodios = int(metadados_spans[1].text.split()[0])
            except:
                numeroEpisodios = None

        if len(metadados_spans) > 2:
            classificacao = metadados_spans[2].text
        nota = float(imdb_li_tag.find_element(By.CLASS_NAME, "ipc-rating-star--rating").text.replace(",", "."))
        link = imdb_li_tag.find_element(By.CLASS_NAME, "ipc-title-link-wrapper").get_attribute("href")

        return Serie(titulo_limpo, anoEstreia, anoEncerramento, numeroEpisodios, classificacao, link, nota, [], None)
    except Exception as e:
        print(f"Problema ao tentar ler dados de uma série: {e}")
        return None

driver = webdriver.Chrome()
driver.get("https://www.imdb.com/pt/chart/toptv/")
driver.maximize_window()

tag_ul = driver.find_element(By.XPATH, r'//*[@id="__next"]/main/div/div[3]/section/div/div[2]/div/ul')
lista_series_tags = tag_ul.find_elements(By.TAG_NAME, "li")

# Processa cada tag de série para criar uma lista de objetos Série
lista_de_series = []
for serie_tag in lista_series_tags:
    serie = cria_serie(serie_tag)
    if serie:
        lista_de_series.append(serie)


lista_de_series_completas = []
for i, dados_base in enumerate(lista_de_series):
        print(f"\n🔄 Processando '{dados_base.titulo}' ({i+1}/{len(lista_de_series)})...")

        elenco, popularidade = buscar_informacoes_adicionais(dados_base.link)

        if elenco is not None or popularidade is not None:
            # Junta os dados básicos com os adicionais
            serie_completa = Serie(
                titulo=dados_base.titulo,
                anoEstreia=dados_base.anoEstreia,
                anoEncerramento=dados_base.anoEncerramento,
                numeroEpisodios=dados_base.numeroEpisodios,
                classificacao=dados_base.classificacao,
                link=dados_base.link,
                nota=dados_base.nota,
                elenco=elenco if elenco is not None else dados_base.elenco,
                popularidade=popularidade if popularidade is not None else dados_base.popularidade
            )
            lista_de_series_completas.append(serie_completa)

# Salva a lista de séries em um arquivo JSON
with open("imdb_top_250_series.json", "w", encoding="utf-8") as arquivo:
    # Converte a lista de objetos para uma lista de dicionários
    lista_series_dict = [serie.__dict__ for serie in lista_de_series_completas]
    json.dump(lista_series_dict, arquivo, ensure_ascii=False, indent=4)

print("Arquivo 'series.json' salvo com sucesso.")

# Fecha o navegador
driver.quit()
