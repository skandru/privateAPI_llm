import litserve as ls
import requests
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import openai


class StockProfitLitAPI(ls.LitAPI):
    def setup(self, device):
        try:
            # Setup your API key for OpenAI and Alpha Vantage
            load_dotenv()
            self.openai_api_key = os.getenv('OPENAI_API_KEY')
            self.av_api_key = os.getenv('AV_API_KEY')
            openai.api_key = self.openai_api_key
        except Exception as e:
            logger.error("Error during setup: %s", str(e))
            raise
    
    def decode_request(self, request):
        try:
            # Decode the JSON request
            return request
        except Exception as e:
            logger.error("Error decoding request: %s", str(e))
            raise
    
    def fetch_stock_data(self, ticker, file_path):
        try:
            fetch_new_data = True
            if os.path.exists(file_path):
                file_mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                if datetime.now() - file_mod_time < timedelta(days=0):
                    fetch_new_data = False
            
            if fetch_new_data:
                url = f'https://www.alphavantage.co/query?function=TIME_SERIES_WEEKLY&symbol={ticker}&apikey={self.av_api_key}&datatype=csv'
                response = requests.get(url)
                
                if response.status_code == 200:
                    os.makedirs('data', exist_ok=True)
                    with open(file_path, 'wb') as file:
                        file.write(response.content)
                    print(f"CSV file has been saved to {file_path}")
                else:
                    print(f"Failed to retrieve data: {response.status_code}")
            else:
                print(f"Using existing CSV file at {file_path}")
        except Exception as e:
            logger.error("Error fetching stock data: %s", str(e))
            raise

    def fetch_stock_splits(self, ticker, split_file_path):
        try:
            if not os.path.exists(split_file_path):
                url = f'https://www.alphavantage.co/query?function=TIME_SERIES_SPLIT&symbol={ticker}&apikey={self.av_api_key}&datatype=csv'
                response = requests.get(url)
                
                if response.status_code == 200:
                    with open(split_file_path, 'wb') as file:
                        file.write(response.content)
                    print(f"Stock split CSV file has been saved to {split_file_path}")
                else:
                    print(f"Failed to retrieve stock split data: {response.status_code}")
            else:
                print(f"Stock split CSV file already exists at {split_file_path}")
        except Exception as e:
            logger.error("Error fetching stock splits: %s", str(e))
            raise

    def adjust_for_splits(self, purchase_date, shares, split_df):
        try:
            purchase_date = datetime.strptime(purchase_date, '%Y-%m-%d')
            adjusted_shares = shares
            for _, split in split_df.iterrows():
                split_date = split['timestamp']
                split_ratio = float(split['stock_split_ratio'].split(':')[1])  # Assuming the format is '1:4'
                if purchase_date < split_date:
                    adjusted_shares *= split_ratio
            return adjusted_shares
        except Exception as e:
            logger.error("Error adjusting for splits: %s", str(e))
            raise

    def get_closest_weekly_price(self, df, purchase_date):
        try:
            purchase_date = datetime.strptime(purchase_date, '%Y-%m-%d')
            closest_date = df.iloc[(df['timestamp'] - purchase_date).abs().argsort()[:1]]
            return closest_date.iloc[0]['timestamp'], closest_date.iloc[0]['close']
        except Exception as e:
            logger.error("Error getting closest weekly price: %s", str(e))
            raise

    def calculate_unrealized_profit(self, ticker, purchase_date, shares):
        try:
            stock_data_file_path = os.path.join('data', f'{ticker}_stock_data.csv')
            split_data_file_path = os.path.join('data', f'{ticker}_stock_splits.csv')

            self.fetch_stock_data(ticker, stock_data_file_path)

            df = pd.read_csv(stock_data_file_path)
            df['timestamp'] = pd.to_datetime(df['timestamp'])

            if os.path.exists(split_data_file_path):
                split_df = pd.read_csv(split_data_file_path)
                split_df['timestamp'] = pd.to_datetime(split_df['timestamp'])
                adjusted_shares = self.adjust_for_splits(purchase_date, shares, split_df)
            else:
                adjusted_shares = shares

            closest_date, purchase_price = self.get_closest_weekly_price(df, purchase_date)
            current_price = df.iloc[0]['close']
            initial_investment = purchase_price * shares
            current_value = current_price * adjusted_shares
            unrealized_profit = current_value - initial_investment

            response = (
                f"Initial investment on {purchase_date} for {shares} shares: ${initial_investment:.2f}\n"
                f"Current value of {shares} shares (adjusted for splits): ${current_value:.2f}\n"
                f"Unrealized profit: ${unrealized_profit:.2f}\n"
            )
            return response
        except Exception as e:
            logger.error("Error calculating unrealized profit: %s", str(e))
            raise


    def predict(self, request):
        try:
            ticker = request['ticker']
            purchase_date = request['purchase_date']
            shares = request['shares']
            
            # Calculate the profit
            calculation_response = self.calculate_unrealized_profit(ticker, purchase_date, shares)
            
            # Generate the chatbot response
            chatbot_prompt = (
                f"I bought {shares} shares of {ticker} stock on {purchase_date}. Can you calculate the profit for me?\n"
                f"{calculation_response}"
                "Please explain this in a simple way."
            )

            chatbot_response = openai.chat.completions.create(
                model="gpt-3.5-turbo",  
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": chatbot_prompt}
                ]
            )
            print (chatbot_response.choices[0].message.content)
            message_content = chatbot_response.choices[0].message.content
            return message_content
          
        except Exception as e:
            logger.error("Error in predict method: %s", str(e))
            raise


    def encode_response(self, response):
        try:
            # Return the chatbot response
            return {"response": response}
        except Exception as e:
            logger.error("Error encoding response: %s", str(e))
            raise

if __name__ == "__main__":
    try:
        api = StockProfitLitAPI()
        server = ls.LitServer(api, accelerator='cuda', devices=1)
        server.run(port=7000)
    except Exception as e:
        logger.error("Error starting server: %s", str(e))
        raise
