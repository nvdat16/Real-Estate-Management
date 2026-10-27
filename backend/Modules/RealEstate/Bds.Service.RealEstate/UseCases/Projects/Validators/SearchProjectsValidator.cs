using Bds.BuildingBlocks.Application.Validation;
using Bds.Domain.RealEstate.Enums;
using Bds.Service.RealEstate.Helpers;
using Bds.Service.RealEstate.UseCases.Projects.Queries;
using FluentValidation;

namespace Bds.Service.RealEstate.UseCases.Projects.Validators;

public sealed class SearchProjectsValidator : AbstractValidator<SearchProjectsQuery>
{
    public SearchProjectsValidator()
    {
        this.AddPagingRules("code", "name", "createdAt");

        RuleFor(x => x.Status)
            .Must(EnumNames.IsDefinedName<ProjectStatus>)
            .WithMessage("Trạng thái phải là Active hoặc Inactive.")
            .When(x => x.Status is not null);
    }
}
