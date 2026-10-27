using Bds.BuildingBlocks.Application.Validation;
using Bds.Service.RealEstate.UseCases.Customers.Queries;
using FluentValidation;

namespace Bds.Service.RealEstate.UseCases.Customers.Validators;

public sealed class SearchCustomersValidator : AbstractValidator<SearchCustomersQuery>
{
    public SearchCustomersValidator()
    {
        this.AddPagingRules("fullName", "createdAt");
    }
}
