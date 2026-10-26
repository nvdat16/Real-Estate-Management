namespace Bds.Model.Dto.RealEstate.Requests;

public sealed record CreatePropertyRequest(
    Guid ProjectId,
    string Code,
    decimal Area,
    int Floor,
    string Position,
    int Bedrooms,
    string Direction);
