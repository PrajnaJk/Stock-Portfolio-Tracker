import yfinance as yf
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Stock Data Fetcher</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
            margin: 0;
            padding: 0;
        }
        .container {
            max-width: 900px;
            margin: 50px auto;
            padding: 20px;
            background-color: #fff;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            border-radius: 8px;
        }
        h1 {
            text-align: center;
            margin-bottom: 20px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        input[type="text"] {
            width: calc(100% - 20px);
            padding: 10px;
            margin: 10px 0;
            border: 1px solid #ccc;
            border-radius: 4px;
        }
        button {
            padding: 10px 15px;
            background-color: #007bff;
            color: #fff;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        button:hover {
            background-color: #0056b3;
        }
        #result {
            margin-top: 20px;
            font-weight: bold;
        }
        #tickers-list {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
            gap: 20px;
        }
        .stock-box {
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            padding: 20px;
            border: 1px solid #ccc;
            border-radius: 4px;
            background-color: #f9f9f9;
        }
        .stock-box h2, .stock-box p {
            margin: 0;
        }
        .red, .red-flash {
            color: #ff0000;
            background-color: #ffe5e5;
        }
        .green, .green-flash {
            color: #00ff00;
            background-color: #e5ffe5;
        }
        .dark-red {
            color: #990000;
        }
        .dark-green {
            color: #009900;
        }
        .gray, .gray-flash {
            color: #808080;
        }
        .red-flash {
            animation: redFlash 0.5s ease-in-out;
        }
        .green-flash {
            animation: greenFlash 0.5s ease-in-out;
        }
        .gray-flash {
            animation: grayFlash 0.5s ease-in-out;
        }
        @keyframes redFlash {
            0% { background-color: #ffe5e5; }
            50% { background-color: #ffcccc; }
            100% { background-color: #ffe5e5; }
        }
        @keyframes greenFlash {
            0% { background-color: #e5ffe5; }
            50% { background-color: #ccffcc; }
            100% { background-color: #e5ffe5; }
        }
        @keyframes grayFlash {
            0% { background-color: #f0f0f0; }
            50% { background-color: #e0e0e0; }
            100% { background-color: #f0f0f0; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Stock Data Fetcher</h1>
        <form id="add-ticker-form">
            <div class="form-group">
                <input type="text" id="new-ticker" placeholder="Enter stock ticker">
                <button type="submit">Add Ticker</button>
            </div>
        </form>
        <div id="tickers-list"></div>
        <div id="result"></div>
        <div>Updating in <span id="counter">15</span> seconds...</div>
    </div>

    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script>
        var tickers = JSON.parse(localStorage.getItem('tickers')) || [];
        var lastPrices = {};
        var counter = 15;

        function startUpdateCycle() {
            updatePrices();
            setInterval(function () {
                counter--;
                $('#counter').text(counter);
                if (counter <= 0) {
                    updatePrices();
                    counter = 15;
                }
            }, 1000);
        }

        $(document).ready(function() {
            console.log("Document is ready");
            tickers.forEach(function(ticker) {
                addTickerToList(ticker);
            });
            updatePrices();
            $('#add-ticker-form').submit(function(e) {
                e.preventDefault();
                var newTicker = $('#new-ticker').val();
                if (newTicker) {
                    newTicker = newTicker.toUpperCase();
                    console.log("Form submitted with ticker:", newTicker);
                    if (!tickers.includes(newTicker)) {
                        tickers.push(newTicker);
                        localStorage.setItem('tickers', JSON.stringify(tickers));
                        addTickerToList(newTicker);
                        console.log("Ticker added:", newTicker);
                    } else {
                        console.log("Ticker already exists:", newTicker);
                    }
                    $('#new-ticker').val('');
                    updatePrices();
                } else {
                    console.log("Ticker input is empty");
                }
            });
            $('#tickers-list').on('click', '.remove-btn', function() {
                var tickerToRemove = $(this).data('ticker');
                tickers = tickers.filter(t => t !== tickerToRemove);
                localStorage.setItem('tickers', JSON.stringify(tickers));
                $(`#${tickerToRemove}`).remove();
                console.log("Ticker removed:", tickerToRemove);
            });
            startUpdateCycle();
        });

        function addTickerToList(ticker) {
            $('#tickers-list').append(`
                <div id="${ticker}" class="stock-box">
                    <h2>${ticker}</h2>
                    <div>
                        <p id="${ticker}-price"></p>
                        <p id="${ticker}-pct"></p>
                    </div>
                    <button class="remove-btn" data-ticker="${ticker}">Remove</button>
                </div>
            `);
        }

        function updatePrices() {
            tickers.forEach(function(ticker) {
                $.ajax({
                    url: '/get_stock_data',
                    type: 'POST',
                    contentType: 'application/json',
                    data: JSON.stringify({'ticker': ticker}),
                    success: function(data) {
                        if (data.error) {
                            console.log("Error fetching data for ticker:", ticker, data.error);
                            return;
                        }
                        var changePercent = ((data.currentPrice - data.openPrice) / data.openPrice) * 100;
                        var colorClass;
                        if (changePercent <= -2) {
                            colorClass = 'dark-red';
                        } else if (changePercent < 0) {
                            colorClass = 'red';
                        } else if (changePercent === 0) {
                            colorClass = 'gray';
                        } else if (changePercent <= 2) {
                            colorClass = 'green';
                        } else {
                            colorClass = 'dark-green';
                        }
                        $(`#${ticker}-price`).text(`$${data.currentPrice.toFixed(2)}`);
                        $(`#${ticker}-pct`).text(`${changePercent.toFixed(2)}%`);
                        $(`#${ticker}-price`).removeClass('dark-red red gray green dark-green').addClass(colorClass);
                        $(`#${ticker}-pct`).removeClass('dark-red red gray green dark-green').addClass(colorClass);

                        var flashClass;
                        if (lastPrices[ticker] > data.currentPrice) {
                            flashClass = 'red-flash';
                        } else if (lastPrices[ticker] < data.currentPrice) {
                            flashClass = 'green-flash';
                        } else {
                            flashClass = 'gray-flash';
                        }
                        lastPrices[ticker] = data.currentPrice;
                        $(`#${ticker}`).addClass(flashClass);
                        setTimeout(function() {
                            $(`#${ticker}`).removeClass(flashClass);
                        }, 1000);
                    }
                });
            });
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/get_stock_data', methods=['POST'])
def get_stock_data():
    ticker = request.get_json().get('ticker', '')
    data = yf.Ticker(ticker).history(period='1d')
    if not data.empty:
        return jsonify({
            'currentPrice': data['Close'].iloc[-1],
            'openPrice': data['Open'].iloc[-1]
        })
    else:
        return jsonify({'error': 'Ticker not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)
