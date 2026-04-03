import pytest
from app.parser import DocType, SomeFilter, find_docs


class Tests:
    def test_parse(self):
        filter = SomeFilter()
        docs = find_docs(filter, start_page=10, end_page=11)

        print(docs[0])

        assert len(docs) > 0 and all(
            (doc.type == DocType.xls or doc.type == DocType.pdf for doc in docs)
        )
