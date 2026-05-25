"""Resolver de política de áudio — SPEC 005.

Calcula a política efetiva de áudio para uma mídia, respeitando a hierarquia:
  midia.audio_policy > campaign.audio_policy > device.audio_policy_default
  > tenant.audio_policy_default > hardcoded 'auto'

O resolver é uma função pura (sem side effects) para facilitar testes.
"""

from typing import Optional


# Valores do enum como strings para evitar dependência circular com models
AUTO = "auto"
RADIO_ONLY = "radio_only"
MEDIA_AUDIO_ONLY = "media_audio_only"
MIX = "mix"
MUTED_VIDEO_WITH_RADIO = "muted_video_with_radio"

_DEFAULT = AUTO


def resolve_effective_audio_policy(
    media_policy: Optional[str],
    campaign_policy: Optional[str],
    device_policy: Optional[str],
    tenant_policy: Optional[str],
) -> str:
    """Retorna a política efetiva seguindo a hierarquia de overrides.

    Args:
        media_policy: audio_policy da mídia (pode ser None).
        campaign_policy: audio_policy da campanha (pode ser None).
        device_policy: audio_policy_default do device (pode ser None).
        tenant_policy: audio_policy_default do tenant (pode ser None).

    Returns:
        String com o valor do enum AudioPolicy que vence.
    """
    for policy in (media_policy, campaign_policy, device_policy, tenant_policy):
        if policy is not None:
            val = policy.value if hasattr(policy, "value") else str(policy)
            if val:
                return val
    return _DEFAULT


def resolve_has_audio(media) -> bool:
    """Retorna se a mídia tem áudio, usando fallback por tipo quando has_audio é None."""
    if media.has_audio is not None:
        return bool(media.has_audio)
    # Fallback: vídeos assumem ter áudio; imagens/url/html não têm.
    media_type = getattr(media, "type", None)
    type_val = media_type.value if hasattr(media_type, "value") else str(media_type or "")
    return type_val.lower() == "video"


def resolve_media_payload(media, campaign, device, tenant) -> dict:
    """Calcula os campos de áudio a incluir no payload do player para uma mídia.

    Returns:
        Dict com 'audio_policy_effective' e 'has_audio'.
    """
    media_policy = getattr(media, "audio_policy", None)
    campaign_policy = getattr(campaign, "audio_policy", None)
    device_policy = getattr(device, "audio_policy_default", None)
    tenant_policy = getattr(tenant, "audio_policy_default", None)

    effective = resolve_effective_audio_policy(
        media_policy, campaign_policy, device_policy, tenant_policy
    )
    has_audio = resolve_has_audio(media)

    return {
        "audio_policy_effective": effective,
        "has_audio": has_audio,
    }


def resolve_campaign_audio_payload(campaign, device, tenant) -> dict:
    """Calcula os campos de áudio a incluir no payload da campanha para o player.

    Returns:
        Dict com 'audio_policy_default' e 'audio_fade_ms'.
    """
    # Política default da campanha: primeira não-nula entre campaign/device/tenant
    campaign_policy = getattr(campaign, "audio_policy", None)
    device_policy = getattr(device, "audio_policy_default", None)
    tenant_policy = getattr(tenant, "audio_policy_default", None)

    effective_default = resolve_effective_audio_policy(
        None, campaign_policy, device_policy, tenant_policy
    )

    fade_ms = getattr(tenant, "audio_fade_ms", None) or 200

    return {
        "audio_policy_default": effective_default,
        "audio_fade_ms": fade_ms,
    }
