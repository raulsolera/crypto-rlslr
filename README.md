# crypto-rlslr

 <font size=2><em>[link](https://github.com/raulsolera/crypto-rlslr/blob/main/README.md) a este documento en github.</em></font> 

Este proyecto se ha realizado como trabajo para la asignatura "Python para Análisis
de datos" del Master en [Big Data Science de la Universidad de Navarra](https://mstr.unav.edu/master-big-data-science/).

### Descripción funcional

El proyecto consiste en mostrar una serie de gráficas de inversión de un par de monedas
(cryptomoneda frente a moneda estándar). Los gráficos que se muestran son el OHLC (Open, High, Low, Close), 
el Vwap y el volumen negociado según se muestra en el siguiente ejemplo:

![project graph](images/project_graph.png)

La información de las cotizaciones se obtiene de [Kraken](https://www.kraken.com/)
llamando a su API pública ([ejemplo](https://api.kraken.com/0/public/Trades?pair=XETHZEUR&since=157406713999999999))
utilizando la librería estándar [urllib.request](https://docs.python.org/3/library/urllib.request.html)
sin necesidad de instalar la [librería propia de kraken](https://support.kraken.com/hc/en-us/articles/360025180232-Kraken-REST-API-command-line-client).
Dado que el proyecto utiliza exclusivamente datos públicos se ha considerado más 
conveniente no tener que hacer instalaciones adicionales.

Si bien para los gráficos OHLC y Volumen negociado existen numerosas referencias,
no es así para el cálculo del Vwap. En este proyecto, por defecto se emplea la versión
que consideramos estándar: precio típico ponderado por volumen acumulado desde
un momento ancla "anchor time" ([ejemplo de cálculo en spreadsheet](https://docs.google.com/spreadsheets/d/143nJ1dhsr6GTQr9Wr8kQby6rOqBGMS9BTrhz5AWNMsY/edit#gid=1559753437)),
método para el cual se han encontrado nuemeros referencias ([investopia](https://www.investopedia.com/terms/v/vwap.asp).
[tradingview](https://www.tradingview.com/scripts/vwap/?solution=43000502018)...),
Sin embargo en el proyecto también se permite la representación del Vwap sin ancla temporal
de referencia (aunque entedemos que en ese caso aporta poca informacón adicional
al gráfico OHLC).

Las referencias estándar para el cálculo del Vwap suelen fijar el ancla temporal
en el inicio de la sesión. En el caso de las criptomonedas (que no cotizan en mercados
con sesiones diarias con apertura y cierre sino que tienen una cotización continua) 
se ha tomado la decisión de permitir fijar el Vwap desde una serie de horas hacia atrás
desde el momento actual. Por defecto se toman -6 horas pero es un parámetro modificable
por el usuario.

Algo caraterístico de estos tres gráficos es que en los tres casos se basan en una
ventana temporal, y por tanto para represetación gráfica por pantalla se ha basado
en un número fijo de ventanas temporales que se ha considerado cómoda (este número
se podría haber dejado como un parámetro de usuario pero de momento se ha fijado
en 90 ventanas completas más la ventana actual (que aún no se ha completado)). Para
clarificar se explicará con un ejemplo:

> Si en el momento de genera el gráfico son las 7:49 horas de la mañana y se ha
> elegido una ventana de 5 minutos, se considera que la última ventana completa termina
> a las 7:45 y desde esa referencia se muestran 90 ventanas completas que son 450
> minutos o 7:30 horas por lo que la hora inicial serán las 0:15 horas.

El tamaño de la ventana se ha fijado por defecto en 5 minutos pero al igual que
el ancla temporal para el cálculo del Vwap puede ser modificado por el usuario.

Por tanto el usuario podrá actuar sobre 3 parámetros: 
* Par de monedas, eligiendo cryptomoneda (de momento ETH - Ethereum, XBT - Bitcoin)
origen y moneda estándar (USD - Dolar, EUR - Euro) destino (por defecto ETH - Ethereum y EUR - Euro)
* Tamaño de la ventana para los gráficos pudiendo eleigir distintas ventanas
desde 30 segundos hasta 15 minutos (por defecto 5 minutos)
* Tiempo ancla (en número de horas hacia atrás) desde el que se fija el acumulado
para el cálculo del Vwap

La aplicación se ejecutará con una serie 

Link a este documento
Instalación
Descripción técnica
limitaciones
Próximos pasos
- utc time
- optimizar get trades
- bells and whistles
- instant (live)


Siempre se representará desde el momento actual hasta el número de
ventanas por el tamaño de la ventana (por ejemplo 100 ventanas de
5 minutos = 500 minutos hacia atrás desde el momento actual)