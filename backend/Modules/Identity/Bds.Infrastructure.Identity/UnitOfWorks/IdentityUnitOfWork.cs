using Bds.BuildingBlocks.Infrastructure.UnitOfWorks;
using Bds.Infrastructure.Identity.Contexts;
using Bds.Infrastructure.Identity.Interfaces;

namespace Bds.Infrastructure.Identity.UnitOfWorks;

public sealed class IdentityUnitOfWork(IdentityContext context) : UnitOfWork<IdentityContext>(context), IIdentityUnitOfWork;
