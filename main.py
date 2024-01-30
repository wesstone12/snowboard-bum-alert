import requests
from bs4 import BeautifulSoup
import os 
api_key = os.environ.get('OPENAI_API_KEY')
from langchain_openai import OpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import ssl

resort_url_map_point_forecast = {
        'Stevens Pass': 'https://forecast.weather.gov/MapClick.php?lat=47.75&lon=-121.09&unit=0&lg=english&FcstType=text&TextType=1',
        'Snoqualmie' :'https://forecast.weather.gov/MapClick.php?lat=47.4187&lon=-121.412&unit=0&lg=english&FcstType=text&TextType=1',
        'Crystal':'https://forecast.weather.gov/MapClick.php?lat=46.9401&lon=-121.4732&unit=0&lg=english&FcstType=text&TextType=2',
        'Mt. Baker':'https://forecast.weather.gov/MapClick.php?lat=48.862&lon=-121.679&unit=0&lg=english&FcstType=text&TextType=1',
        'Mission Ridge':'https://forecast.weather.gov/MapClick.php?lat=47.3022&lon=-120.3925&unit=0&lg=english&FcstType=text&TextType=1'
    }



def get_response(url):
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the HTML content of the page
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Identify and extract the desired data
        # For example, to get all text within <p> tags:# Find all bold tags, as they seem to precede the forecast descriptions
    forecast_entries = soup.find_all('b')

    # Initialize a list to hold each forecast entry
    forecasts = []

    for entry in forecast_entries:
        # Use find_next_sibling to safely get the next text element
        forecast_text = entry.find_next_sibling(string=True)
        
        # Check if forecast_text is not None before stripping
        if forecast_text:
            forecast_text = forecast_text.strip()
            full_forecast = f"{entry.get_text()}: {forecast_text}"
            forecasts.append(full_forecast)
        else:
            # Handle cases where there is no following text
            forecasts.append(entry.get_text() + ": No further details.")

    return forecasts


def langchain(responses):
    prompt = PromptTemplate(
    input_variables=['responses'],
    template = '''Tell me about the forecast, but talk like a mega snowboard bum. I wanna know about the weather
    at Stevens Pass, Snoqualmie, Crystal, Mt. Baker, and Mission Ridge. 'resort':'forecast' so it will be easy to do
     a quick scan.
     
    FORECASTS:{responses}
     
    ***TASK***: Write a summary of the forecast for each resort. Talk like a snowboard bum. Be funny and entertaining, but accurate. Be concise.
     
     ''')
        
    llm = OpenAI(temperature=.7, max_tokens = 1000)
    chain = LLMChain(llm=llm, prompt=prompt)

    return chain.invoke(input=responses)['text']

def send_email(message):
    username = os.environ.get('EMAIL')
    password = os.environ.get('PASSWORD')
    smtp_server = 'smtp.gmail.com'
    smtp_port = 465  # SSL port
    sender_email = username
    receiver_email = username
    subject = 'Snowboard Update brah'
    body = message

    # Set up the email message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))


    context = ssl.create_default_context()
    # Send the email using SSL
    try:
        with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
            server.login(username, password)  # Log in to the SMTP server
            server.sendmail(sender_email, 'maddy.marietta@gmail.com', msg.as_string())  # Send the email
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

def main():



    responses = []
    for resort, url in resort_url_map_point_forecast.items():
        res = get_response(url)
        responses.append({resort:res})
    # print(responses)s
    res = langchain(responses)
    print(res) 
    send_email(res)

    
   
        

if __name__ == "__main__":
    main()