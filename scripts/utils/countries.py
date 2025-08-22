EXCLUDED = {"RU", "UA", "BY", "AM", "AZ", "KZ", "KG", "TJ", "TM", "UZ"}

ALL_COUNTRIES = [
    "US","CA","MX","BR","AR","CL","CO","PE","VE","UY","PY","BO","EC","GT","CR","PA","DO","PR","SV","HN","NI","JM","BS","CU",
    "GB","IE","FR","DE","IT","ES","PT","NL","BE","LU","CH","AT","DK","NO","SE","FI","IS","PL","CZ","SK","HU","RO","BG","GR",
    "MD","SI","HR","BA","RS","ME","MK","AL","LT","LV","EE",
    "TR","CY","MT",
    "IL","SA","AE","QA","KW","BH","OM","JO","LB","PS","EG","MA","DZ","TN","LY","SD","KE","NG","GH","CI","SN","UG","TZ","ZM",
    "ZW","MZ","AO","CM","ET","RW","BW","NA","ZA",
    "IN","CN","JP","KR","HK","TW","SG","MY","TH","VN","PH","ID","BN","KH","LA","MM",
    "AU","NZ",
]
COUNTRIES = [c for c in ALL_COUNTRIES if c not in EXCLUDED]