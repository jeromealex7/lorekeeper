from .feature import Feature


class Page(Feature):
    TABLE_NAME = 'page'
    _book: int
    list_index: int
    name: str
    text: str

    def get_charts(self) -> list[int]:
        df = self.keep.buildings['chart'].df.sort_values(by='list_index')
        return df[df['_page'] == self.db_index]['_chart'].values.tolist()

    def get_footnotes(self) -> list[int]:
        df = self.keep.buildings['footnote'].df.sort_values(by='list_index')
        return df[df['_page'] == self.db_index]['_footnote'].values.tolist()

    def get_sigils(self) -> list[int]:
        df = self.keep.buildings['sigil'].df.sort_values(by='list_index')
        return df[df['_page'] == self.db_index]['_sigil'].values.tolist()
