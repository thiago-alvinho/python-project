import processador
import scrapper
import validacao

if __name__ == "__main__":
    scrapper.scrapping()
    processador.processar_tudo()
    validacao.executar_pipeline()