namespace Bds.Model.Dto.RealEstate.Responses;

public sealed record PropertyResponse(
    Guid Id,
    Guid ProjectId,
    string ProjectCode,
    string ProjectName,
    string Code,
    decimal Area,
    int Floor,
    string Position,
    int Bedrooms,
    string Direction,
    string Status,
    DateTime CreatedAt);
