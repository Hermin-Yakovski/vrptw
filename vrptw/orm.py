from typing import TYPE_CHECKING

from or_scenario import orm
from or_scenario.orm import DimParameter, DimSnapshot, DimVersion, Fact

if TYPE_CHECKING:
    from sqlalchemy import Engine


DimWeekday = orm.generate_dimension_table("Weekday")
DimDay = orm.generate_dimension_table("Day",
    weekday=orm.generate_extra_column("weekday", "integer", foreign_key='dim_weekday.id', nullable=False),
)
# dimension tables
## universal: weekday, month etc.
## pass

## administrative areas
# DimProvince = orm.generate_dimension_table("Province")
# DimCity = orm.generate_dimension_table("City",
#     province_id=orm.generate_extra_column("province_id", "integer", foreign_key='dim_province.id', nullable=False),
# )
# DimDistrict = orm.generate_dimension_table("District",
#     province_id=orm.generate_extra_column("province_id", "integer", foreign_key='dim_province.id', nullable=False),
#     city_id=orm.generate_extra_column("city_id", "integer", foreign_key='dim_city.id', nullable=False),
# )
# DimArea = orm.generate_dimension_table("Area",
#     city_id=orm.generate_extra_column("city_id", "integer", foreign_key='dim_city.id', nullable=False),
#     district_id=orm.generate_extra_column("district_id", "integer", foreign_key='dim_district.id'),
#     start_house_id=orm.generate_extra_column("start_house_id", "integer", foreign_key='dim_house.id', nullable=False),
# )    # either a city or a district

# wms
DimHouse = orm.generate_dimension_table("House")
DimHouseVector = orm.generate_dimension_table("HouseVector",
    tail=orm.generate_extra_column("tail", "integer", foreign_key='dim_house.id', nullable=False),
    head=orm.generate_extra_column("head", "integer", foreign_key='dim_house.id', nullable=False),
)
DimRegion = orm.generate_dimension_table("Region",
    admin_level=orm.generate_extra_column("admin_level", "integer", nullable=False),
)

# derivatives of HouseVector
DimLine = orm.generate_dimension_table("Line",
    grade=orm.generate_extra_column("grade", "integer", nullable=False),
    tail=orm.generate_extra_column("tail", "integer", foreign_key='dim_house.id',nullable=False),
    head=orm.generate_extra_column("head", "integer", foreign_key='dim_house.id', nullable=False),
)
DimSegment = orm.generate_dimension_table("Segment",
    line_id=orm.generate_extra_column("line_id", "integer", foreign_key='dim_line.id', nullable=False),
    housevector_id=orm.generate_extra_column("housevector_id", "integer", foreign_key='dim_housevector.id', nullable=False),
    sequence=orm.generate_extra_column('sequence', 'integer', nullable=False),
)

## tms
# DimSegment = orm.generate_dimension_table("Segment",
#     head=orm.generate_extra_column("head_house_id", "integer", foreign_key='dim_house.id', nullable=False),
#     tail=orm.generate_extra_column("tail_house_id", "integer", foreign_key='dim_house.id', nullable=False),
#     # transport_time=orm.generate_extra_column("transport_time", "integer"),
#     # cycle=orm.generate_extra_column("cycle", "string_64", default='1,2,3,4,5,6,7'),
# )
# DimUrban = orm.generate_dimension_table("Urban",
#     start_house_id=orm.generate_extra_column("start_house_id", "integer", foreign_key='dim_house.id', nullable=False),
#     area_id=orm.generate_extra_column("area_id", "integer", foreign_key='dim_area.id', nullable=False),
#     transport_time=orm.generate_extra_column("transport_time", "integer"),
#     cycle=orm.generate_extra_column("cycle", "string_64", default='1,2,3,4,5,6,7'),
# )

## oms
# DimBill = orm.generate_dimension_table("Bill",
#     start_house_id=orm.generate_extra_column("start_house_id", "integer", foreign_key='dim_house.id', nullable=False),
#     # end_house_id=orm.generate_extra_column("end_house_id", "integer"),
#     # end_province_id=orm.generate_extra_column("end_province_id", "integer"),
#     # end_city_id=orm.generate_extra_column("end_city_id", "integer"),
#     # end_district_id=orm.generate_extra_column("end_district_id", "integer"),
#     end_house_id=orm.generate_extra_column("end_area_id", "integer", foreign_key='dim_house.id', nullable=False),
# )

# fact tables
# FactAreaBill = orm.generate_fact_table("Area", "Bill")
# FactBill = orm.generate_fact_table("Bill")
# FactArea = orm.generate_fact_table("Area")
FactHouseVector = orm.generate_fact_table("HouseVector")
FactHouseRegion = orm.generate_fact_table("House", "Region")
FactLineWeekday = orm.generate_fact_table("Line", "Weekday")
FactSegmentWeekday = orm.generate_fact_table("Segment", "Weekday")

# sol tables
# SolAreaBill = orm.generate_sol_table("Area", "Bill")
SolDayHouseVector = orm.generate_sol_table("Day", "HouseVector")
SolLine = orm.generate_sol_table("Line")


__all__ = [
    'DimSnapshot', 'DimVersion', 'DimParameter', "Fact",
    'DimWeekday', 'DimDay',
    # 'DimProvince', 'DimCity', 'DimDistrict', 'DimArea',
    'DimHouse', 'DimHouseVector', 'DimRegion',
    'DimLine', 'DimSegment',

    'FactHouseVector', 'FactHouseRegion', 'FactLineWeekday', 'FactSegmentWeekday',

    'SolDayHouseVector', 'SolLine',
]
