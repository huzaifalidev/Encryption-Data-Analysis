import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.units import inch

# Function to generate dashboard using ReportLab instead of FPDF to avoid Unicode issues
def generate_encryption_dashboard():
    print("Starting dashboard generation...")
    
    # Load the benchmark results - try original files first since that's what's causing the error
    try:
        print("Attempting to load original CSV files...")
        df_detailed = pd.read_csv('encryption_detailed_results.csv')
        df_summary = pd.read_csv('encryption_summary.csv')
        print("Successfully loaded original data files")
    except FileNotFoundError:
        print("Original files not found, trying benchmark files...")
        try:
            df_detailed = pd.read_csv('encryption_benchmark_detailed.csv')
            df_summary = pd.read_csv('encryption_benchmark_summary.csv')
            print("Successfully loaded benchmark data")
        except FileNotFoundError:
            print("No benchmark data found. Please run the benchmark script first.")
            return
    
    # Create the visualizations first
    print("Creating visualizations...")
    
    # Create visualization: Encryption and Decryption Time
    algorithms = df_summary['Algorithm'].tolist()
    enc_times = df_summary['Encryption Time (s)'].tolist()
    dec_times = df_summary['Decryption Time (s)'].tolist()
    
    x = np.arange(len(algorithms))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(10, 6))
    enc_bars = ax.bar(x - width/2, enc_times, width, label='Encryption Time')
    dec_bars = ax.bar(x + width/2, dec_times, width, label='Decryption Time')
    
    ax.set_title('Encryption vs Decryption Time by Algorithm')
    ax.set_xlabel('Algorithm')
    ax.set_ylabel('Time (seconds)')
    ax.set_xticks(x)
    ax.set_xticklabels(algorithms)
    ax.legend()
    
    plt.tight_layout()
    plt.savefig('enc_dec_time_comparison.png', dpi=300)
    plt.close()
    
    # Create visualization: Key Size and Ciphertext Size on logarithmic scale
    fig, ax = plt.subplots(figsize=(10, 6))
    
    key_sizes = df_summary['Key Size (bits)'].tolist()
    cipher_sizes = df_summary['Ciphertext Size'].tolist()
    
    x = np.arange(len(algorithms))
    width = 0.35
    
    ax.bar(x - width/2, key_sizes, width, label='Key Size (bits)')
    ax.bar(x + width/2, cipher_sizes, width, label='Ciphertext Size (bytes)')
    
    ax.set_title('Key Size vs Ciphertext Size by Algorithm')
    ax.set_xlabel('Algorithm')
    ax.set_ylabel('Size (log scale)')
    ax.set_yscale('log')
    ax.set_xticks(x)
    ax.set_xticklabels(algorithms)
    ax.legend()
    
    plt.tight_layout()
    plt.savefig('key_cipher_size_comparison.png', dpi=300)
    plt.close()
    
    # Box plot of encryption times across emails for each algorithm
    plt.figure(figsize=(12, 6))
    sns.boxplot(x='Algorithm', y='Encryption Time (s)', data=df_detailed)
    plt.title('Distribution of Encryption Times by Algorithm')
    plt.tight_layout()
    plt.savefig('encryption_time_distribution.png', dpi=300)
    plt.close()
    
    # Security vs Performance Trade-off
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Define security score (higher is more secure)
    security_scores = []
    for _, row in df_summary.iterrows():
        # Calculate security score based on key size and quantum resistance
        quantum_factor = 2 if row['Quantum-Resistant'] else 1
        key_size_factor = np.log10(row['Key Size (bits)']) / 5  # Normalize
        security_scores.append(quantum_factor * (0.5 + key_size_factor))
    
    # Create performance score (lower is better)
    performance_scores = []
    for _, row in df_summary.iterrows():
        # Lower times and sizes are better for performance
        time_factor = (row['Encryption Time (s)'] + row['Decryption Time (s)']) / 2
        size_factor = np.log10(row['Ciphertext Size']) / 10  # Normalize
        performance_scores.append(-(time_factor + size_factor))  # Negative because lower is better
    
    # Create scatter plot
    sc = ax.scatter(performance_scores, security_scores, s=100, c=range(len(algorithms)), cmap='viridis')
    
    # Add labels for each point
    for i, alg in enumerate(algorithms):
        ax.annotate(alg, (performance_scores[i], security_scores[i]), 
                   xytext=(5, 5), textcoords='offset points')
    
    ax.set_title('Security vs Performance Trade-off')
    ax.set_xlabel('Performance (higher is better)')
    ax.set_ylabel('Security (higher is better)')
    
    plt.tight_layout()
    plt.savefig('security_performance_tradeoff.png', dpi=300)
    plt.close()
    
    print("Visualizations created successfully")
    
    # Calculate some metrics for the findings
    fastest_enc = df_summary.loc[df_summary['Encryption Time (s)'].idxmin(), 'Algorithm']
    fastest_dec = df_summary.loc[df_summary['Decryption Time (s)'].idxmin(), 'Algorithm']
    smallest_key = df_summary.loc[df_summary['Key Size (bits)'].idxmin(), 'Algorithm']
    smallest_cipher = df_summary.loc[df_summary['Ciphertext Size'].idxmin(), 'Algorithm']
    quantum_algos = df_summary[df_summary['Quantum-Resistant'] == True]['Algorithm'].tolist()
    
    # Now create the PDF with ReportLab
    print("Creating PDF with ReportLab...")
    pdf_filename = 'encryption_algorithms_dashboard.pdf'
    doc = SimpleDocTemplate(pdf_filename, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Create a list to hold the content
    content = []
    
    # Title
    title_style = styles['Title']
    content.append(Paragraph("Encryption Algorithms Benchmark", title_style))
    content.append(Spacer(1, 12))
    
    # Introduction
    intro_style = styles['Normal']
    intro_text = "This dashboard presents a comparative analysis of encryption algorithms, including traditional (AES, RSA) and post-quantum (Kyber, McEliece) approaches. The benchmark tests were performed on email data to measure performance and security characteristics."
    content.append(Paragraph(intro_text, intro_style))
    content.append(Spacer(1, 12))
    
    # Summary Table heading
    heading_style = ParagraphStyle(
        'Heading1',
        parent=styles['Heading1'],
        fontSize=16,
    )
    content.append(Paragraph("Algorithm Comparison Summary", heading_style))
    content.append(Spacer(1, 12))
    
    # Format the summary table
    quantum_resistant = {True: 'Yes', False: 'No'}
    table_data = [['Algorithm', 'Enc Time (s)', 'Dec Time (s)', 'Quantum-Resistant', 
                  'Best Use Case', 'Cipher Size', 'Key Size (bits)']]
    
    for _, row in df_summary.iterrows():
        table_data.append([
            row['Algorithm'],
            f"{row['Encryption Time (s)']:.6f}",
            f"{row['Decryption Time (s)']:.6f}",
            quantum_resistant.get(row['Quantum-Resistant'], str(row['Quantum-Resistant'])),
            row['Best Use Case'],
            f"{int(row['Ciphertext Size'])}",
            f"{int(row['Key Size (bits)'])}"
        ])
    
    # Create table
    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    content.append(table)
    content.append(Spacer(1, 24))
    
    # Add images
    # Encryption and Decryption Time Chart
    content.append(Paragraph("Encryption vs Decryption Time", heading_style))
    content.append(Spacer(1, 12))
    content.append(Image('enc_dec_time_comparison.png', width=7*inch, height=4*inch))
    content.append(Spacer(1, 24))
    
    # Key Size and Ciphertext Size Chart
    content.append(Paragraph("Key Size vs Ciphertext Size (Log Scale)", heading_style))
    content.append(Spacer(1, 12))
    content.append(Image('key_cipher_size_comparison.png', width=7*inch, height=4*inch))
    content.append(Spacer(1, 24))
    
    # Distribution of Encryption Times
    content.append(Paragraph("Distribution of Encryption Times", heading_style))
    content.append(Spacer(1, 12))
    content.append(Image('encryption_time_distribution.png', width=7*inch, height=4*inch))
    content.append(Spacer(1, 24))
    
    # Security vs Performance Tradeoff
    content.append(Paragraph("Security vs Performance Trade-off", heading_style))
    content.append(Spacer(1, 12))
    content.append(Image('security_performance_tradeoff.png', width=7*inch, height=4*inch))
    content.append(Spacer(1, 24))
    
    # Key Findings and Recommendations
    content.append(Paragraph("Key Findings and Recommendations", heading_style))
    content.append(Spacer(1, 12))
    
    findings = [
        f"• {fastest_enc} provides the fastest encryption times, making it ideal for performance-critical applications.",
        f"• {fastest_dec} offers the quickest decryption, which is important for real-time data access.",
        f"• {smallest_key} uses the smallest key size, requiring less storage for key management.",
        f"• {smallest_cipher} produces the smallest ciphertext, minimizing bandwidth and storage requirements.",
        f"• {', '.join(quantum_algos)} {'are' if len(quantum_algos) > 1 else 'is'} quantum-resistant, providing future-proofing against quantum computing threats.",
        "• For sensitive data requiring long-term security, quantum-resistant algorithms are recommended despite the performance trade-offs.",
        "• AES remains the most efficient choice for bulk data encryption where quantum resistance is not a concern.",
        "• A hybrid approach combining classical and post-quantum algorithms may provide the best balance of security and performance."
    ]
    
    for finding in findings:
        content.append(Paragraph(finding, styles['Normal']))
        content.append(Spacer(1, 6))
    
    content.append(Spacer(1, 12))
    
    # Conclusion
    content.append(Paragraph("Conclusion", heading_style))
    content.append(Spacer(1, 12))
    
    conclusion = (
        "This benchmark demonstrates the trade-offs between classical and post-quantum encryption algorithms. "
        "While classical algorithms like AES and RSA offer excellent performance, they are vulnerable to quantum computing attacks. "
        "Post-quantum algorithms provide future-proof security but at the cost of larger key sizes and ciphertexts. "
        "Organizations should consider their specific security requirements, data sensitivity, and performance needs when selecting encryption algorithms. "
        "A strategic approach might involve using classical algorithms for everyday operations while beginning the transition to quantum-resistant algorithms for sensitive and long-lived data."
    )
    content.append(Paragraph(conclusion, styles['Normal']))
    
    # Build and save the PDF
    doc.build(content)
    print(f"PDF dashboard saved as '{pdf_filename}'")

if __name__ == "__main__":
    generate_encryption_dashboard()