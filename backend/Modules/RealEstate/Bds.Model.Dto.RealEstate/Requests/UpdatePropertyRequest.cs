namespace Bds.Model.Dto.RealEstate.Requests;

public sealed record UpdatePropertyRequest(
    decimal Area,
    int Floor,
    string Position,
    int Bedrooms,
    string Direction);
