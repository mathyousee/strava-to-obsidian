"""Command-line interface for Strava to Obsidian exporter."""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import click

from strava_to_obsidian import __version__
from strava_to_obsidian.api import StravaAPIError, StravaClient
from strava_to_obsidian.auth import authenticate, ensure_valid_token
from strava_to_obsidian.config import Config
from strava_to_obsidian.exporter import ActivityExporter
from strava_to_obsidian.models import Activity


@click.group()
@click.version_option(version=__version__)
@click.pass_context
def main(ctx: click.Context) -> None:
    """Export Strava activities to Obsidian-flavored Markdown files."""
    ctx.ensure_object(dict)
    ctx.obj["config"] = Config.load()


@main.command()
@click.pass_context
def auth(ctx: click.Context) -> None:
    """Authenticate with Strava via OAuth."""
    config: Config = ctx.obj["config"]

    if not config.has_valid_credentials():
        click.echo("❌ Missing Strava API credentials.")
        click.echo("")
        click.echo("Set these environment variables:")
        click.echo("  export STRAVA_CLIENT_ID='your_client_id'")
        click.echo("  export STRAVA_CLIENT_SECRET='your_client_secret'")
        click.echo("")
        click.echo("Get your credentials at: https://www.strava.com/settings/api")
        raise SystemExit(1)

    try:
        click.echo("🔐 Starting Strava authentication...")
        tokens = authenticate(config)
        if tokens:
            click.echo(f"✅ Authenticated as {tokens.athlete_name} (ID: {tokens.athlete_id})")
            click.echo(f"   Tokens saved to {config.token_file}")
    except ValueError as e:
        click.echo(f"❌ Authentication failed: {e}")
        raise SystemExit(1)


@main.command()
@click.option(
    "--output", "-o",
    type=click.Path(path_type=Path),
    default=Path("./activities"),
    help="Output directory for exported files",
)
@click.option(
    "--days", "-d",
    type=int,
    default=30,
    help="Export activities from the last N days",
)
@click.option(
    "--after",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="Export activities after this date (YYYY-MM-DD)",
)
@click.option(
    "--before",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="Export activities before this date (YYYY-MM-DD)",
)
@click.option(
    "--force", "-f",
    is_flag=True,
    help="Overwrite existing files",
)
@click.option(
    "--no-media",
    is_flag=True,
    help="Skip downloading photos",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be exported without writing files",
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Show detailed output",
)
@click.pass_context
def export(
    ctx: click.Context,
    output: Path,
    days: int,
    after: Optional[datetime],
    before: Optional[datetime],
    force: bool,
    no_media: bool,
    dry_run: bool,
    verbose: bool,
) -> None:
    """Export activities to Markdown files."""
    config: Config = ctx.obj["config"]

    # Check authentication
    if not config.has_tokens():
        click.echo("❌ Not authenticated. Run 'strava-to-obsidian auth' first.")
        raise SystemExit(1)

    if not ensure_valid_token(config):
        click.echo("❌ Token refresh failed. Run 'strava-to-obsidian auth' to re-authenticate.")
        raise SystemExit(1)

    # Set date range
    if not after:
        after = datetime.now() - timedelta(days=days)
    if not before:
        before = datetime.now()

    click.echo(f"📅 Exporting activities from {after.date()} to {before.date()}")
    click.echo(f"📁 Output directory: {output.absolute()}")
    if dry_run:
        click.echo("🔍 DRY RUN - no files will be written")
    click.echo("")

    # Initialize API client and exporter
    client = StravaClient(config)
    exporter = ActivityExporter(output)

    if not dry_run:
        exporter.setup_directories()

    # Fetch and export activities
    try:
        click.echo("📥 Fetching activity list from Strava...")
        activities_list = list(client.get_activities(after=after, before=before))
        click.echo(f"   Found {len(activities_list)} activities")
        click.echo("")

        exported = 0
        skipped = 0
        failed = 0

        with click.progressbar(
            activities_list,
            label="Exporting activities",
            show_pos=True,
        ) as bar:
            for activity_summary in bar:
                activity_id = activity_summary["id"]
                activity_name = activity_summary.get("name", "Untitled")

                try:
                    # Get detailed activity data
                    detail = client.get_activity_detail(activity_id)
                    activity = Activity.from_api_response(detail)

                    # Check if exists
                    if not force and exporter.activity_exists(activity):
                        skipped += 1
                        if verbose:
                            click.echo(f"   ⏭️  Skipped (exists): {activity_name}")
                        continue

                    # Export
                    if dry_run:
                        exported += 1
                        if verbose:
                            click.echo(f"   📝 Would export: {activity_name}")
                    else:
                        filepath = exporter.export_activity(
                            activity,
                            force=force,
                            download_photo=not no_media,
                        )
                        if filepath:
                            exported += 1
                            if verbose:
                                click.echo(f"   ✅ Exported: {activity_name}")
                        else:
                            skipped += 1

                except StravaAPIError as e:
                    failed += 1
                    if verbose:
                        click.echo(f"   ❌ Failed: {activity_name} - {e}")

        click.echo("")
        click.echo(f"✅ Export complete!")
        click.echo(f"   Exported: {exported}")
        click.echo(f"   Skipped:  {skipped}")
        if failed > 0:
            click.echo(f"   Failed:   {failed}")
        click.echo(f"   {client.get_rate_limit_status()}")

    except StravaAPIError as e:
        click.echo(f"❌ API Error: {e}")
        raise SystemExit(1)


@main.command()
@click.option(
    "--output", "-o",
    type=click.Path(path_type=Path),
    default=Path("./activities"),
    help="Output directory for exported files",
)
@click.option(
    "--force", "-f",
    is_flag=True,
    help="Overwrite existing files",
)
@click.option(
    "--no-media",
    is_flag=True,
    help="Skip downloading photos",
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Show detailed output",
)
@click.pass_context
def sync(
    ctx: click.Context,
    output: Path,
    force: bool,
    no_media: bool,
    verbose: bool,
) -> None:
    """Sync new activities (incremental export)."""
    # For now, sync is the same as export with default 30 days
    # Future: track last sync time and only fetch new activities
    ctx.invoke(
        export,
        output=output,
        days=30,
        force=force,
        no_media=no_media,
        verbose=verbose,
    )


@main.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    """Show authentication and sync status."""
    config: Config = ctx.obj["config"]

    click.echo("Strava to Obsidian Status")
    click.echo("=" * 40)

    # Credentials
    if config.has_valid_credentials():
        click.echo(f"✅ API credentials configured")
        click.echo(f"   Client ID: {config.strava.client_id[:8]}...")
    else:
        click.echo("❌ API credentials not configured")
        click.echo("   Set STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET")

    # Tokens
    if config.has_tokens():
        click.echo(f"✅ OAuth tokens present")
        click.echo(f"   Token file: {config.token_file}")

        # Check if valid
        if ensure_valid_token(config):
            click.echo("✅ Access token is valid")

            # Get athlete info
            try:
                client = StravaClient(config)
                athlete = client.get_athlete()
                name = f"{athlete.get('firstname', '')} {athlete.get('lastname', '')}".strip()
                click.echo(f"   Logged in as: {name}")
                click.echo(f"   {client.get_rate_limit_status()}")
            except StravaAPIError as e:
                click.echo(f"⚠️  Could not fetch athlete info: {e}")
        else:
            click.echo("⚠️  Access token expired, needs refresh")
    else:
        click.echo("❌ Not authenticated")
        click.echo("   Run 'strava-to-obsidian auth' to authenticate")


if __name__ == "__main__":
    main()
