from typing import List, Optional
from fastapi import Request
from sqlalchemy import desc, asc
from sqlalchemy.orm import Query

# Pagination Model
class PaginationParams:
    def __init__(self, skip: int = 0, limit: int = 10, sort_field: Optional[str] = None, sort_order: Optional[str] = "asc"):
        self.skip = skip
        self.limit = limit
        self.sort_field = sort_field
        self.sort_order = sort_order

    def get_query(self, query: Query):
        # Apply sorting if sort_field is specified
        if self.sort_field:
            if self.sort_order == "desc":
                query = query.order_by(desc(self.sort_field))
            else:
                query = query.order_by(asc(self.sort_field))
        
        # Apply pagination (skip and limit)
        query = query.offset(self.skip).limit(self.limit)
        return query


# Pagination & Sorting Helper Function
def paginate_and_sort(query: Query, pagination_params: PaginationParams) -> Query:
    return pagination_params.get_query(query)
