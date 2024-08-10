from attrs import define, field
from typing import List, ClassVar, Optional


@define
class PrismCentalCredentials:
    kind: ClassVar[str] = "prism_central_credentials"
    name: str = field(
        metadata={"description": "A NickName/Identifier for Prism Central"}
    )
    endpoint: str = field(
        metadata={
            "description": "Nutanix Prism Central endpoint, without scheme or port."
        }
    )
    username: str = field(metadata={"description": "Nutanix Prism Central username."})
    password: str = field(metadata={"description": "Nutanix Prism Central password."})
    insecure: Optional[bool] = field(
        default=False,
        metadata={"description": "Whether to ignore SSL certificate errors."},
    )
    port: Optional[int] = field(
        default=9440,
        metadata={"description": "Nutanix Prism Central port."},
    )


@define
class PrismCentralColletorConfig:
    kind: ClassVar[str] = "prism_central"
    credentials: List[PrismCentalCredentials] = field(
        factory=list,
        metadata={
            "description": "Nutanix Prism Central credentials for the resources to be collected."
            "Expected format: [{ 'name': 'my_pc', 'endpoint': 'mypc.example.com', 'insecure': 'true', 'port': '9440', 'username':'my_pc_username', 'password':'my_pc_password'}]."
        },
    )
