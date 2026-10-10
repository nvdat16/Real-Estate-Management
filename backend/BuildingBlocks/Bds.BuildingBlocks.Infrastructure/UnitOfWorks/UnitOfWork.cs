using Bds.BuildingBlocks.Application.Abstractions;
using Microsoft.EntityFrameworkCore;

namespace Bds.BuildingBlocks.Infrastructure.UnitOfWorks;

public abstract class UnitOfWork<TContext>(TContext context) : IUnitOfWork
    where TContext : DbContext
{
    protected TContext Context { get; } = context;

    public Task<int> SaveChangesAsync(CancellationToken cancellationToken = default)
        => Context.SaveChangesAsync(cancellationToken);
}
