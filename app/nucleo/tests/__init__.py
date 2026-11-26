from django.conf import settings

# D-298: com a chave ligada, toda cascata de LP de 2026 nasceria com o seed dos Word (pendências e hashes
# diferentes, imagens gravadas no media/). Desligada aqui; test_cascata_infografico religa.
# ponytail: setting mudado no import do pacote de testes; com mais chaves assim, um TEST_RUNNER próprio
settings.INFOGRAFICOS_DO_SEED = False
