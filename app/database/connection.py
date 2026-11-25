
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv(dotenv_path="./config/.env")


class Neo4jConnection:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI")
        self.username = os.getenv("NEO4J_USERNAME")
        self.password = os.getenv("NEO4J_PASSWORD")
        print("URI:", os.getenv("NEO4J_URI"))
        print("USERNAME:", os.getenv("NEO4J_USERNAME"))
        print("PASSWORD EXISTS:", bool(os.getenv("NEO4J_PASSWORD")))
        print("PASSWORD LENGTH:", len(os.getenv("NEO4J_PASSWORD") or ""))
        self.driver = None

    def connect(self):
        """Khởi tạo và kiểm tra kết nối Neo4j."""

        if self.driver is not None:
            return self.driver

        if not all([self.uri, self.username, self.password]):
            raise ValueError(
                "Thiếu cấu hình kết nối Neo4j trong file .env"
            )

        driver = GraphDatabase.driver(
            self.uri,
            auth=(self.username, self.password)
        )

        try:
            driver.verify_connectivity()
            self.driver = driver

            print("Kết nối Neo4j thành công!")

            return self.driver

        except Exception:
            driver.close()
            raise

    def get_driver(self):
        if self.driver is None:
            return self.connect()

        return self.driver

    def close(self):
        if self.driver is not None:
            self.driver.close()
            self.driver = None
            print("Đã đóng kết nối Neo4j.")



