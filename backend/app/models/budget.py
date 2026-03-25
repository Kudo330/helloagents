from pydantic import BaseModel, Field, field_validator


class Budget(BaseModel):
    """预算信息"""
    total_attractions: int = Field(default=0, ge=0, description="景点门票总费用")
    total_hotels: int = Field(default=0, ge=0, description="酒店总费用")
    total_meals: int = Field(default=0, ge=0, description="餐饮总费用")
    total_transportation: int = Field(default=0, ge=0, description="交通总费用")
    total: int = Field(default=0, ge=0, description="总费用")

    @field_validator('total')
    @classmethod
    def validate_total(cls, v, info):
        """验证总费用的正确性"""
        if v is None:
            return v

        # 确保总费用等于各分项之和
        data = info.data
        if data:
            expected_total = (
                data.get('total_attractions', 0) +
                data.get('total_hotels', 0) +
                data.get('total_meals', 0) +
                data.get('total_transportation', 0)
            )
            # 允许小的差异（四舍五入）
            if abs(v - expected_total) > 1:
                # 如果差异太大，使用计算值
                return expected_total
        return v
