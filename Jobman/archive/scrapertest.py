import requests

url = "https://ch.indeed.com/jobs?q=ICT"
r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})

print(r.status_code)
print("job_seen_beacon" in r.text)