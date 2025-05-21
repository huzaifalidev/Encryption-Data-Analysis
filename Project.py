# Simple script to ensure the benchmark runs before the dashboard
import pandas as pd
import time
import os

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP, AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad

print("Starting encryption benchmark...")

# Check if there's a CSV file to read
try:
    df = pd.read_csv('./emails.csv')
    emails = df['message'].dropna().head(20)  # Test on exactly 20 emails
    print(f"Loaded {len(emails)} emails for testing")
except FileNotFoundError:
    print("emails.csv not found, using dummy data for testing")
    # Create some dummy data if the CSV doesn't exist
    emails = [
        "This is a test email message " + "test content " * 20 + str(i) 
        for i in range(20)
    ]

# Encryption algorithms with decryption
def aes_encrypt_decrypt(text):
    key = get_random_bytes(16)  # 128-bit key
    cipher = AES.new(key, AES.MODE_CBC)
    iv = cipher.iv
    
    # Encryption
    start_encrypt = time.time()
    ciphertext = cipher.encrypt(pad(text.encode(), AES.block_size))
    end_encrypt = time.time()
    encrypt_time = end_encrypt - start_encrypt
    
    # Decryption
    start_decrypt = time.time()
    cipher_decrypt = AES.new(key, AES.MODE_CBC, iv)
    plaintext = unpad(cipher_decrypt.decrypt(ciphertext), AES.block_size)
    end_decrypt = time.time()
    decrypt_time = end_decrypt - start_decrypt
    
    return {
        'Ciphertext Size': len(ciphertext),
        'Encryption Time (s)': encrypt_time,
        'Decryption Time (s)': decrypt_time,
        'Key Size (bits)': len(key) * 8,
        'Quantum-Resistant': False,
        'Best Use Case': 'Bulk Data Encryption'
    }

def rsa_encrypt_decrypt(text):
    key = RSA.generate(2048)
    cipher_rsa = PKCS1_OAEP.new(key.publickey())
    
    # Generate AES key for hybrid encryption
    aes_key = get_random_bytes(32)
    
    # Encryption
    start_encrypt = time.time()
    # Encrypt email with AES
    cipher_aes = AES.new(aes_key, AES.MODE_EAX)
    nonce = cipher_aes.nonce
    ciphertext, tag = cipher_aes.encrypt_and_digest(text.encode())
    # Encrypt AES key with RSA
    encrypted_aes_key = cipher_rsa.encrypt(aes_key)
    end_encrypt = time.time()
    encrypt_time = end_encrypt - start_encrypt
    
    # Decryption
    start_decrypt = time.time()
    # Decrypt AES key with RSA
    cipher_rsa_decrypt = PKCS1_OAEP.new(key)
    aes_key_decrypted = cipher_rsa_decrypt.decrypt(encrypted_aes_key)
    # Decrypt data with AES
    cipher_aes_decrypt = AES.new(aes_key_decrypted, AES.MODE_EAX, nonce=nonce)
    plaintext = cipher_aes_decrypt.decrypt_and_verify(ciphertext, tag)
    end_decrypt = time.time()
    decrypt_time = end_decrypt - start_decrypt
    
    return {
        'Ciphertext Size': len(ciphertext) + len(encrypted_aes_key),
        'Encryption Time (s)': encrypt_time,
        'Decryption Time (s)': decrypt_time,
        'Key Size (bits)': 2048,
        'Quantum-Resistant': False,
        'Best Use Case': 'Secure Key Exchange'
    }

def kyber_encrypt_decrypt(text):
    # Simulated Kyber encryption/decryption (real would use liboqs-python)
    # Encryption
    start_encrypt = time.time()
    time.sleep(0.003)  # Simulate encryption delay
    ciphertext_size = len(text) + 100  # Simulated ciphertext size
    end_encrypt = time.time()
    encrypt_time = end_encrypt - start_encrypt
    
    # Decryption
    start_decrypt = time.time()
    time.sleep(0.002)  # Simulate decryption delay (typically faster than encryption)
    end_decrypt = time.time()
    decrypt_time = end_decrypt - start_decrypt
    
    return {
        'Ciphertext Size': ciphertext_size,
        'Encryption Time (s)': encrypt_time,
        'Decryption Time (s)': decrypt_time,
        'Key Size (bits)': 1536,
        'Quantum-Resistant': True,
        'Best Use Case': 'Post-Quantum TLS'
    }

def mceliece_encrypt_decrypt(text):
    # Simulated McEliece encryption/decryption
    # Encryption
    start_encrypt = time.time()
    time.sleep(0.005)  # Simulate encryption delay
    ciphertext_size = len(text) * 1.8  # Simulated ciphertext size
    end_encrypt = time.time()
    encrypt_time = end_encrypt - start_encrypt
    
    # Decryption
    start_decrypt = time.time()
    time.sleep(0.008)  # Simulate decryption delay (typically slower than encryption)
    end_decrypt = time.time()
    decrypt_time = end_decrypt - start_decrypt
    
    return {
        'Ciphertext Size': int(ciphertext_size),
        'Encryption Time (s)': encrypt_time,
        'Decryption Time (s)': decrypt_time,
        'Key Size (bits)': 1357824,  # 1.3MB key
        'Quantum-Resistant': True,
        'Best Use Case': 'Post-Quantum Secure Messaging'
    }

# Run all algorithms
results = []
print("Running benchmark tests...")
for i, email in enumerate(emails):
    if i % 5 == 0:
        print(f"Processing email {i+1}/{len(emails)}")
    for name, func in [
        ('AES', aes_encrypt_decrypt), 
        ('RSA', rsa_encrypt_decrypt),
        ('Kyber', kyber_encrypt_decrypt), 
        ('McEliece', mceliece_encrypt_decrypt)
    ]:
        result = func(email)
        results.append({
            'Email ID': i + 1,
            'Algorithm': name,
            **result  # Unpack all the metrics
        })

# Create DataFrame from results
df_results = pd.DataFrame(results)

# Calculate averages for each algorithm
avg_results = df_results.groupby('Algorithm').mean(numeric_only=True)
avg_results = avg_results.reset_index()

# Add the non-numeric columns back
for algo in avg_results['Algorithm']:
    for col in ['Quantum-Resistant', 'Best Use Case']:
        # Get the first occurrence as they should all be the same for each algorithm
        value = df_results[df_results['Algorithm'] == algo][col].iloc[0]
        avg_results.loc[avg_results['Algorithm'] == algo, col] = value

# Round numeric columns for better readability
numeric_cols = ['Encryption Time (s)', 'Decryption Time (s)', 'Ciphertext Size', 'Key Size (bits)']
avg_results[numeric_cols] = avg_results[numeric_cols].round(6)

# Reorder columns for the final summary
final_cols = ['Algorithm', 'Encryption Time (s)', 'Decryption Time (s)', 'Quantum-Resistant', 
              'Best Use Case', 'Ciphertext Size', 'Key Size (bits)']
avg_results = avg_results[final_cols]

# Save detailed results to new CSV files
df_results.to_csv('encryption_benchmark_detailed.csv', index=False)

# Save the summary with averages to new CSV file
avg_results.to_csv('encryption_benchmark_summary.csv', index=False)

print("\n=== Summary Results (Averages) ===\n")
print(avg_results)

print("\nBenchmark completed! Results saved to 'encryption_benchmark_detailed.csv' and 'encryption_benchmark_summary.csv'")
print("Now run the dashboard generator to create the PDF report.")