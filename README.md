# Relógio Mundial

Um relógio de mesa minimalista para Linux (KDE Plasma) que mostra a hora de um país escolhido lado a lado com o horário de Brasília, incluindo o fuso horário e a diferença de horas entre os dois.

![Screenshot do Relógio Mundial](docs/screenshot.png)

## Funcionalidades

- Hora em tempo real do país selecionado, ao lado da hora de Brasília
- Fuso horário (UTC±X) e diferença de horas calculados automaticamente (considera horário de verão)
- Cerca de 40 países pré-cadastrados, com bandeira e busca pelo seletor
- Design escuro, minimalista, com cantos arredondados e sombra suave
- Janela sem borda, arrastável, sempre visível por cima das outras (opcional)
- Lembra o último país escolhido entre uma execução e outra

## Requisitos

- Linux com sessão gráfica (testado no Fedora com KDE Plasma / Wayland)
- Python 3.9+
- [PySide6](https://pypi.org/project/PySide6/)

## Instalação

```bash
git clone https://github.com/<seu-usuario>/world-clock.git
cd world-clock
pip install -r requirements.txt
```

## Uso

```bash
python3 world_clock.py
```

- Clique no nome do país (sublinhado tracejado) para trocar o país
- Clique e arraste em qualquer área vazia da janela para mover
- Clique no "×" no canto superior direito para fechar

### Atalho no menu de aplicativos (KDE Plasma)

Para abrir pelo menu do Plasma como qualquer outro programa, crie o arquivo `~/.local/share/applications/world-clock.desktop` com o seguinte conteúdo (ajuste o caminho do `Exec` para onde você clonou o projeto):

```ini
[Desktop Entry]
Type=Application
Name=Relógio Mundial
Comment=Hora de países do mundo comparada ao horário de Brasília
Exec=python3 /caminho/completo/para/world-clock/world_clock.py
Icon=clock
Terminal=false
Categories=Utility;Clock;
```

Depois rode `update-desktop-database ~/.local/share/applications` e procure por "Relógio Mundial" no menu.

## Adicionando ou removendo países

A lista de países fica no início de [world_clock.py](world_clock.py), na constante `COUNTRIES`. Cada item é uma tupla `(nome exibido, fuso IANA, código ISO do país)`:

```python
("Portugal", "Europe/Lisbon", "PT"),
```

O código de duas letras é usado para gerar a bandeira automaticamente — não precisa adicionar emoji manualmente. Fusos horários seguem a [lista de zonas IANA](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).

## Tecnologia

- [PySide6](https://doc.qt.io/qtforpython/) (Qt6) para a interface
- `zoneinfo` (biblioteca padrão do Python) para os cálculos de fuso horário

## Licença

Distribuído sob a licença MIT. Veja [LICENSE](LICENSE) para mais detalhes.
