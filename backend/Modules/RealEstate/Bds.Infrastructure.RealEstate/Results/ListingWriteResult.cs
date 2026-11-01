namespace Bds.Infrastructure.RealEstate.Results;

// Values must match the p_result codes returned by the realestate.sp_listing_* procedures.
public enum ListingWriteResult
{
    Success = 0,
    NotFound = 1,
    NotOwner = 2,
    InvalidStatus = 3,
    AgentProfileRequired = 4,
    PropertyNotFound = 5,
    PropertyNotAvailable = 6,
    PropertyHasActiveListing = 7,
}
