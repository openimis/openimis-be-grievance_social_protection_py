"""
Management command to view and manage grievance permissions.
"""
import json
import logging
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from grievance_social_protection.models import Ticket
from grievance_social_protection.apps import TicketConfig

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Manage grievance permissions in Django auth_permission table'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            type=str,
            choices=['list', 'cleanup', 'export', 'sync'],
            help='Action to perform'
        )
        parser.add_argument(
            '--format',
            type=str,
            default='table',
            choices=['table', 'json', 'csv'],
            help='Output format for list/export actions'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes'
        )

    def handle(self, *args, **options):
        action = options['action']
        
        if action == 'list':
            self.list_permissions(options['format'])
        elif action == 'cleanup':
            self.cleanup_permissions(options['dry_run'])
        elif action == 'export':
            self.export_permissions(options['format'])
        elif action == 'sync':
            self.sync_permissions(options['dry_run'])

    def list_permissions(self, format_type):
        # Get content type for Ticket model
        try:
            ct = ContentType.objects.get_for_model(Ticket)
        except Exception as e:
            logger.warning(f"Could not get ContentType for Ticket model: {e}")
            return
    
        """List all grievance permissions"""
        perms = Permission.objects.filter(
            content_type=ct,
            codename__endswith='_grievance',
            id__range=(127100, 127999)
        ).order_by('id')
        
        if format_type == 'table':
            self.stdout.write("\nGrievance Permissions:")
            self.stdout.write("-" * 80)
            self.stdout.write(f"{'ID':<8} {'Codename':<50} {'Name':<30}")
            self.stdout.write("-" * 80)
            
            for perm in perms:
                self.stdout.write(f"{perm.id:<8} {perm.codename:<50} {perm.name[:30]:<30}")
            
            self.stdout.write("-" * 80)
            self.stdout.write(f"Total: {perms.count()} permissions\n")
            
        elif format_type == 'json':
            data = [
                {
                    'id': perm.id,
                    'codename': perm.codename,
                    'name': perm.name
                }
                for perm in perms
            ]
            self.stdout.write(json.dumps(data, indent=2))
            
        elif format_type == 'csv':
            self.stdout.write("ID,Codename,Name")
            for perm in perms:
                self.stdout.write(f'{perm.id},"{perm.codename}","{perm.name}"')

    def cleanup_permissions(self, dry_run):
        """Remove orphaned permissions not in current configuration"""
        # Get current configuration
        configured_perms = set()
        
        # Collect configured category permissions
        for cat_name, cat_info in TicketConfig.processed_categories.items():
            perms = cat_info.get('permissions', [])
            if isinstance(perms, dict):
                perms = list(perms.keys())
            safe_name = cat_name.lower().replace(' ', '_').replace('|', '_')
            for perm_type in perms:
                codename = f"{perm_type}_{safe_name}_grievance"
                configured_perms.add(codename)
        
        # Collect configured flag permissions
        for flag_name, flag_info in TicketConfig.processed_flags.items():
            perms = flag_info.get('permissions', [])
            if isinstance(perms, dict):
                perms = list(perms.keys())
            safe_name = flag_name.lower().replace(' ', '_')
            for perm_type in perms:
                codename = f"{perm_type}_flag_{safe_name}_grievance"
                configured_perms.add(codename)
        
        # Get content type for Ticket model
        try:
            ct = ContentType.objects.get_for_model(Ticket)
        except Exception as e:
            logger.warning(f"Could not get ContentType for Ticket model: {e}")
            return
    
        # Find orphaned permissions
        all_perms = Permission.objects.filter(
            content_type=ct,
            codename__endswith='_grievance',
            id__range=(127100, 127999)
        )
        
        orphaned = []
        for perm in all_perms:
            if perm.codename not in configured_perms:
                orphaned.append(perm)
        
        if not orphaned:
            self.stdout.write(self.style.SUCCESS("No orphaned permissions found."))
            return
        
        self.stdout.write(f"\nFound {len(orphaned)} orphaned permission(s):")
        for perm in orphaned:
            self.stdout.write(f"  - {perm.id}: {perm.codename}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("\nDry run - no changes made."))
        else:
            confirm = input("\nDelete these permissions? (yes/no): ")
            if confirm.lower() == 'yes':
                count = len(orphaned)
                for perm in orphaned:
                    perm.delete()
                self.stdout.write(self.style.SUCCESS(f"Deleted {count} permission(s)."))
            else:
                self.stdout.write("Cleanup cancelled.")

    def export_permissions(self, format_type):
        """Export permission mapping for backup"""
        data = {
            'base_permissions': {},
            'category_permissions': {},
            'flag_permissions': {}
        }
        
        # Export base permissions
        base_perms = Permission.objects.filter(
            id__range=(127000, 127099)
        )
        for perm in base_perms:
            data['base_permissions'][perm.codename] = perm.id
        
        # Export category permissions
        for cat_name, cat_info in TicketConfig.processed_categories.items():
            if cat_info.get('generated_rights'):
                data['category_permissions'][cat_name] = cat_info['generated_rights']
        
        # Export flag permissions
        for flag_name, flag_info in TicketConfig.processed_flags.items():
            if flag_info.get('generated_rights'):
                data['flag_permissions'][flag_name] = flag_info['generated_rights']
        
        if format_type == 'json':
            self.stdout.write(json.dumps(data, indent=2))
        else:
            self.stdout.write("\nPermission Export:")
            self.stdout.write("=" * 60)
            self.stdout.write("\nBase Permissions:")
            for code, id in data['base_permissions'].items():
                self.stdout.write(f"  {code}: {id}")
            
            self.stdout.write("\nCategory Permissions:")
            for cat, perms in data['category_permissions'].items():
                self.stdout.write(f"  {cat}:")
                for ptype, pid in perms.items():
                    self.stdout.write(f"    {ptype}: {pid}")
            
            self.stdout.write("\nFlag Permissions:")
            for flag, perms in data['flag_permissions'].items():
                self.stdout.write(f"  {flag}:")
                for ptype, pid in perms.items():
                    self.stdout.write(f"    {ptype}: {pid}")

    def sync_permissions(self, dry_run):
        """Sync permissions with current configuration"""
        try:
            ct = ContentType.objects.get_for_model(Ticket)
        except Exception as e:
            raise CommandError(f"Could not get ContentType: {e}")
        
        created = []
        existing = []
        
        # Check category permissions
        for cat_name, cat_info in TicketConfig.processed_categories.items():
            perms = cat_info.get('permissions', [])
            if isinstance(perms, dict):
                perms = list(perms.keys())
            
            safe_name = cat_name.lower().replace(' ', '_').replace('|', '_')
            for perm_type in perms:
                codename = f"grievance_{safe_name}_{perm_type}"
                name = f"Can {perm_type.replace('_', ' ')} {cat_name} tickets"
                
                if Permission.objects.filter(codename=codename, content_type=ct).exists():
                    existing.append(codename)
                else:
                    created.append((codename, name))
        
        # Check flag permissions
        for flag_name, flag_info in TicketConfig.processed_flags.items():
            perms = flag_info.get('permissions', [])
            if isinstance(perms, dict):
                perms = list(perms.keys())
            
            safe_name = flag_name.lower().replace(' ', '_')
            for perm_type in perms:
                codename = f"grievance_flag_{safe_name}_{perm_type}"
                name = f"Can {perm_type.replace('_', ' ')} {flag_name} flagged tickets"
                
                if Permission.objects.filter(codename=codename, content_type=ct).exists():
                    existing.append(codename)
                else:
                    created.append((codename, name))
        
        self.stdout.write(f"\nPermission Sync Summary:")
        self.stdout.write(f"  Existing: {len(existing)} permissions")
        self.stdout.write(f"  To create: {len(created)} permissions")
        
        if created:
            self.stdout.write("\nPermissions to create:")
            for codename, name in created:
                self.stdout.write(f"  - {codename}: {name}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("\nDry run - no changes made."))
        else:
            if created:
                confirm = input("\nCreate these permissions? (yes/no): ")
                if confirm.lower() == 'yes':
                    # This will trigger the auto-generation in apps.py
                    self.stdout.write("\nTriggering permission generation...")
                    TicketConfig._TicketConfig__generate_automatic_rights()
                    self.stdout.write(self.style.SUCCESS("Permissions synchronized."))
                else:
                    self.stdout.write("Sync cancelled.")
            else:
                self.stdout.write(self.style.SUCCESS("All permissions are up to date."))