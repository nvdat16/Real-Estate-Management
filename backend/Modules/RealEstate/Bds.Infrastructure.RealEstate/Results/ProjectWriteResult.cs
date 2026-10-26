namespace Bds.Infrastructure.RealEstate.Results;

// Values must match the p_result codes returned by the realestate.sp_project_* procedures.
public enum ProjectWriteResult
{
    Success = 0,
    NotFound = 1,
    CodeExists = 2,
    DistrictNotInProvince = 3,
    HasProperties = 4,
}
