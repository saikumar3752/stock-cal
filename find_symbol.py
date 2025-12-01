import json

def find_correct_symbol():
    print("🔍 Searching for correct symbols...")
    
    try:
        with open("instrument_keys.json", "r") as f:
            data = json.load(f)
            
        # Search for "TATA" and "ZOMATO" and "ETERNAL"
        search_terms = ["TATA", "ZOMATO", "ETERNAL"]
        
        found_counts = 0
        print("\n--- RESULTS ---")
        for symbol, key in data.items():
            for term in search_terms:
                if term in symbol:
                    print(f"✅ Found: {symbol}  ->  {key}")
                    found_counts += 1
                    
        if found_counts == 0:
            print("❌ No matches found. The instrument file might be empty or corrupt.")
            
    except Exception as e:
        print(f"Error reading file: {e}")

if __name__ == "__main__":
    find_correct_symbol()