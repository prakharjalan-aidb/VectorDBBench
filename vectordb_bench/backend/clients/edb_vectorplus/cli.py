import os
from typing import Annotated, Unpack

import click
from pydantic import SecretStr

from vectordb_bench.backend.clients import DB

from ....cli.cli import (
    CommonTypedDict,
    IVFFlatTypedDict,
    cli,
    click_parameter_decorators_from_typed_dict,
    get_custom_case_config,
    run,
)


class EdbVectorplusTypedDict(CommonTypedDict):
    user_name: Annotated[
        str,
        click.option("--user-name", type=str, help="Db username", required=True),
    ]
    password: Annotated[
        str,
        click.option(
            "--password",
            type=str,
            help="Postgres database password",
            default=lambda: os.environ.get("POSTGRES_PASSWORD", ""),
            show_default="$POSTGRES_PASSWORD",
        ),
    ]
    host: Annotated[str, click.option("--host", type=str, help="Db host", required=True)]
    port: Annotated[
        int,
        click.option(
            "--port",
            type=int,
            help="Postgres database port",
            default=5432,
            show_default=True,
            required=False,
        ),
    ]
    db_name: Annotated[str, click.option("--db-name", type=str, help="Db name", required=True)]
    maintenance_work_mem: Annotated[
        str | None,
        click.option(
            "--maintenance-work-mem",
            type=str,
            help="Sets the maximum memory to be used for maintenance operations (index creation). "
            "Can be entered as string with unit like '64GB' or as an integer number of KB."
            "This will set the parameters: max_parallel_maintenance_workers,"
            " max_parallel_workers & table(parallel_workers)",
            required=False,
        ),
    ]
    max_parallel_workers: Annotated[
        int | None,
        click.option(
            "--max-parallel-workers",
            type=int,
            help="Sets the maximum number of parallel processes per maintenance operation (index creation)",
            required=False,
        ),
    ]


class EdbVectorplusIVFPlusTypedDict(EdbVectorplusTypedDict, IVFFlatTypedDict):
    lists: Annotated[int | None, click.option("--lists", type=int, help="ivfplus lists")]
    probes: Annotated[int | None, click.option("--probes", type=int, help="ivfplus probes")]
    rotation: Annotated[
        bool,
        click.option(
            "--rotation/--no-rotation",
            type=bool,
            help="Apply ivfplus's rotation preprocessing step",
            default=True,
            show_default=True,
        ),
    ]
    iterative_scan: Annotated[
        str | None,
        click.option(
            "--iterative-scan",
            type=str,
            help="ivfplus.iterative_scan session GUC value",
            required=False,
        ),
    ]
    max_probes: Annotated[
        int | None,
        click.option(
            "--max-probes",
            type=int,
            help="ivfplus.max_probes session GUC value",
            required=False,
        ),
    ]
    hierarchy_threshold: Annotated[
        int | None,
        click.option(
            "--hierarchy-threshold",
            type=int,
            help="ivfplus.hierarchy_threshold session GUC value",
            required=False,
        ),
    ]


@cli.command()
@click_parameter_decorators_from_typed_dict(EdbVectorplusIVFPlusTypedDict)
def EdbVectorplusIVFPlus(
    **parameters: Unpack[EdbVectorplusIVFPlusTypedDict],
):
    from .config import EdbVectorplusConfig, EdbVectorplusIvfplusIndexConfig

    parameters["custom_case"] = get_custom_case_config(parameters)
    run(
        db=DB.EdbVectorplus,
        db_config=EdbVectorplusConfig(
            db_label=parameters["db_label"],
            user_name=SecretStr(parameters["user_name"]),
            password=SecretStr(parameters["password"]),
            host=parameters["host"],
            port=parameters["port"],
            db_name=parameters["db_name"],
        ),
        db_case_config=EdbVectorplusIvfplusIndexConfig(
            metric_type=None,
            lists=parameters["lists"],
            probes=parameters["probes"],
            rotation=parameters["rotation"],
            iterative_scan=parameters["iterative_scan"],
            max_probes=parameters["max_probes"],
            hierarchy_threshold=parameters["hierarchy_threshold"],
            maintenance_work_mem=parameters["maintenance_work_mem"],
            max_parallel_workers=parameters["max_parallel_workers"],
        ),
        **parameters,
    )
