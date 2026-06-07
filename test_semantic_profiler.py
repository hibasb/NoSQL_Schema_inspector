import datetime
from semantic_profiler import SemanticProfiler, export_report_json, export_report_csv, generate_pdf_report

def run_test():
    print("Initializing test documents...")
    docs = [
        # Normal doc
        {
            "id": 1,
            "email": "john.doe@example.com",
            "phone": "+1-555-0199",
            "price": 19.99,
            "total": 39.98,
            "paid": True,
            "status": "delivered",
            "delivery_date": "2026-06-01T12:00:00Z",
            "birth_date": "1990-05-15",
            "age": 36,
            "items": [
                {"price": 19.99, "qty": 2}
            ],
            "created_at": "2026-01-01T00:00:00Z"
        },
        # Violating doc 1: malformed email, negative price, fake boolean, ancient date
        {
            "id": 2,
            "email": "invalid-email-address",
            "phone": "123", # too short
            "price": -5.0,
            "total": 0.0,
            "paid": "true", # fake bool
            "status": "delivered", # missing delivery_date
            "birth_date": "1990-05-15",
            "age": 20, # age vs birth_date mismatch
            "created_at": "1999-12-31T23:59:59Z", # ancient date
            "items": []
        },
        # Violating doc 2: zero value, future date, suspicious default, empty string
        {
            "id": 3,
            "email": "admin@test.com",
            "phone": "555-abcd", # has letters
            "price": 0.0, # ZeroValue violation
            "total": 100.0,
            "paid": False,
            "status": "pending",
            "birth_date": "2026-07-07", # future date
            "age": None,
            "description": "   ", # empty string
            "comment": "TODO: fix this value", # suspicious default
            "items": [
                {"price": 10.0, "qty": 5} # items total is 50, but total is 100 -> inconsistent
            ]
        }
    ]

    print("Running profiler...")
    profiler = SemanticProfiler(docs, "test_collection")
    report = profiler.profile()

    print(f"Collection Name: {report.collection_name}")
    print(f"Total Documents: {report.total_documents}")
    print(f"Total Fields Analyzed: {report.total_fields_analyzed}")
    print(f"Quality Score: {report.quality_score:.2f}")
    print(f"Grade: {report.grade}")
    
    print("\n--- FINDINGS ---")
    for f in report.findings:
        print(f"[{f.severity}] Field: '{f.field_path}' | Rule: '{f.rule_name}' | Affected: {f.affected_count}/{f.total_count} ({f.affected_rate:.1f}%)")
        print(f"   Examples: {f.examples}")
        print(f"   Suggestion: {f.suggestion}")

    print("\nTesting exports...")
    json_out = export_report_json(report)
    print("JSON export length:", len(json_out))
    
    df_out = export_report_csv(report)
    print("CSV export dimensions:", df_out.shape)
    
    pdf_out = generate_pdf_report(report)
    print("PDF export size:", len(pdf_out), "bytes")
    
    # Save the PDF to a test file
    with open("test_report.pdf", "wb") as pdf_file:
        pdf_file.write(pdf_out)
    print("Saved test_report.pdf successfully!")

if __name__ == "__main__":
    run_test()
