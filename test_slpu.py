import requests

url = 'http://127.0.0.1:8000/slpu' 

svg_input = '''<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512">
</svg>'''

headers = {'Content-Type': 'image/svg+xml'}

response = requests.post(url, data=svg_input, headers=headers)

print("Status code:", response.status_code)
print("Response SVG:")
print(response.text)
