namespace Bds.Infrastructure.RealEstate.Results;

// Values must match the p_result codes returned by the realestate.sp_property_* procedures.
public enum PropertyWriteResult
{
    Success = 0,
    NotFound = 1,
    CodeExists = 2,
    ProjectInactive = 3,
    ProjectNotFound = 4,
    NotAvailable = 5,
}
