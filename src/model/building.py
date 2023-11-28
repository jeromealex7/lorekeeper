from typing import Type, TypeVar

import pandas as pd

Feature = TypeVar('Feature')
Keep = TypeVar('Keep')


class Building:

    def __init__(self, keep: Keep, feature_type: Type[Feature]):
        self.df = pd.DataFrame(columns=list(feature_type.get_default_data().keys()))
        self.df.index.rename('_index', inplace=True)
        self.keep = keep
        self.is_modified = False
        self.feature_type = feature_type

    def reset_columns(self):
        if not self.df.empty:
            return
        for column in list(self.feature_type.get_default_data().keys()):
            self.df[column] = pd.Series()

    @classmethod
    def read_keep(cls, keep: Keep, feature_type: Type[Feature]):
        building = cls(keep=keep, feature_type=feature_type)
        try:
            sql_result = pd.read_sql(f'SELECT * FROM {feature_type.TABLE_NAME}', con=keep.connection,
                                     index_col='_index')
            not_null_mask = sql_result.notnull().all(axis=1)
            building.df = sql_result[not_null_mask]
        except pd.errors.DatabaseError:
            pass
        return building

    def save(self, modified_only: bool = True):
        if modified_only and not self.is_modified:
            return
        self.df.to_sql(name=self.feature_type.TABLE_NAME, con=self.keep.connection, if_exists='replace')
        self.is_modified = False
