import google.generativeai as genai
genai.configure(api_key="AQ.Ab8RN6K6E4NPJWn7J-0W2eaJDFhtQ_b8CxF4Z0Ds846WnrAA1g")
for m in genai.list_models():
    if "embedContent" in m.supported_generation_methods:
        print(m.name)