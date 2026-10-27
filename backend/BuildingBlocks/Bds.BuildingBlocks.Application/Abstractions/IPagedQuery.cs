using Bds.BuildingBlocks.Application.Models;

namespace Bds.BuildingBlocks.Application.Abstractions;

public interface IPagedQuery
{
    PageOptions Paging { get; }
}
