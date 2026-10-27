namespace Bds.Infrastructure.RealEstate.Results;

// Values must match the p_result codes returned by realestate.sp_customer_upsert and sp_agent_upsert.
public enum ProfileWriteResult
{
    Success = 0,
    LicenseExists = 2,
}
