def connect_neo4j():
    from neo4j import GraphDatabase

    URI = "neo4j+s://5e8a567c.databases.neo4j.io"
    USERNAME = "5e8a567c"
    PASSWORD = "LPht7m3RjZsUvJNGeuiXEt2emHn9o-OHWPtfqcnsWYE"

    driver = GraphDatabase.driver(
        URI,
        auth=(USERNAME, PASSWORD)
    )

    # Kiểm tra kết nối
    try:
        driver.verify_connectivity()
        print("Kết nối Neo4j thành công!")

    except Exception as e:
        print("Kết nối Neo4j thất bại:")
        print(e)

    return driver

if __name__ == "__main__":
    driver = connect_neo4j()
    input_path =  "/content/drive/MyDrive/Project/Xet_Khen_Thuong/Result/GLiNER-ner-rel/results.json"

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)