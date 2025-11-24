#!/usr/bin/env python3
"""
Script para contar inquilinos (doctores) registrados en el sistema.
"""
import asyncio
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.session import get_session
from database.repositories.user_repository import DoctorRepository
from config import SUPER_ADMIN_ID

async def count_tenants():
    """Cuenta y muestra los inquilinos registrados."""
    async with get_session() as session:
        doctor_repo = DoctorRepository(session)
        
        # Obtener todos los doctores (activos e inactivos)
        all_doctors = await doctor_repo.get_all_doctors()
        
        # Filtrar el SuperAdmin
        tenants = [doc for doc in all_doctors if doc.telegram_id != SUPER_ADMIN_ID]
        
        # Separar activos e inactivos
        active_tenants = [t for t in tenants if t.is_active]
        inactive_tenants = [t for t in tenants if not t.is_active]
        
        print("=" * 60)
        print("📊 INQUILINOS REGISTRADOS")
        print("=" * 60)
        print(f"\n✅ Activos: {len(active_tenants)}")
        print(f"❌ Inactivos: {len(inactive_tenants)}")
        print(f"📦 Total: {len(tenants)}")
        
        if active_tenants:
            print("\n" + "-" * 60)
            print("✅ INQUILINOS ACTIVOS:")
            print("-" * 60)
            for i, tenant in enumerate(active_tenants, 1):
                print(f"{i}. ID: {tenant.id} | Nombre: {tenant.name} | Telegram ID: {tenant.telegram_id}")
        
        if inactive_tenants:
            print("\n" + "-" * 60)
            print("❌ INQUILINOS INACTIVOS:")
            print("-" * 60)
            for i, tenant in enumerate(inactive_tenants, 1):
                print(f"{i}. ID: {tenant.id} | Nombre: {tenant.name} | Telegram ID: {tenant.telegram_id}")
        
        print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(count_tenants())

