using Bds.BuildingBlocks.Infrastructure.UnitOfWorks;
using Bds.Infrastructure.RealEstate.Contexts;
using Bds.Infrastructure.RealEstate.Interfaces;

namespace Bds.Infrastructure.RealEstate.UnitOfWorks;

public sealed class RealEstateUnitOfWork(RealEstateContext context) : UnitOfWork<RealEstateContext>(context), IRealEstateUnitOfWork;
