# Media Forge For Codex Native

Use this workflow to gather, generate, process, and upload media required by
the demo plan.

## Objectives

- collect or generate assets needed by media fields
- normalize formats and sizes
- upload assets when the target app requires hosted media
- eliminate external hotlinks from the final mapping where possible

## Outputs

- `.allforai/demo-forge/assets/`
- `.allforai/demo-forge/assets-manifest.json`
- `.allforai/demo-forge/upload-mapping.json`

## Downgrade rules

- if search or generation providers are unavailable, state which classes of
  media could not be fulfilled
- if upload capability is unavailable, report that the media pipeline is
  incomplete rather than claiming success
