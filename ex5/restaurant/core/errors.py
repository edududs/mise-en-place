"""A família de erros do restaurante.

Módulo separado porque TODO mundo importa erro, e erro não deve arrastar
dependência nenhuma junto. Um `except` por consequência de negócio, e a
hierarquia permite pegar a família inteira quando isso fizer sentido.
"""

from __future__ import annotations


class RestaurantError(Exception):
    """Base do domínio."""


class InvalidOrderError(RestaurantError):
    """Fronteira: o pedido não entra. Recusa na hora, não improvisa."""


class ItemNotOnMenuError(InvalidOrderError):
    """A mesa pediu algo que o restaurante não serve."""


class WrongCourseError(InvalidOrderError):
    """Pediu chopp como prato principal: o item existe, o curso está errado."""


class EmptyRoundError(InvalidOrderError):
    """Comanda sem item nenhum."""


class PartyTooLargeError(InvalidOrderError):
    """Mais gente do que a mesa suporta."""


class LeftTheQueueError(RestaurantError):
    """O grupo esperou mais que a própria paciência e foi embora.

    Não é erro do restaurante nem do cliente: é uma SAÍDA legítima do fluxo,
    modelada como exceção porque interrompe a jornada inteira da mesa.
    """


class DishBurnedError(RestaurantError):
    """Risco de OPERAÇÃO (não da receita): o item se perde e é refeito."""


class UnknownStationError(RestaurantError):
    """A receita pede uma estação que esta praça não tem: erro de montagem.

    Não é erro do cliente nem do cozinheiro — é o artefato DENUNCIANDO drift
    entre o cardápio e o inventário físico. Falha alto, na primeira execução.
    """


class RestaurantClosedError(RestaurantError):
    """Chegou pedido com o restaurante fechado."""
