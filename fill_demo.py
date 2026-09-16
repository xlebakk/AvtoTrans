"""
Скрипт заполнения БД демо-данными для всех разделов системы.
Запуск: py fill_demo.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date, timedelta
from app.database import Base, engine, SessionLocal
from app.models import (
    Client, Driver, DriverStatus, Vehicle, VehicleStatus,
    CargoRequest, Order, OrderStatus
)
from sqlalchemy import select

Base.metadata.create_all(bind=engine)

def run():
    with SessionLocal() as db:
        # Очистим существующие данные (кроме машин и водителей — они уже есть)
        db.query(Order).delete()
        db.query(CargoRequest).delete()
        db.query(Driver).delete()
        db.query(Client).delete()
        db.query(Vehicle).delete()
        db.commit()

        # ── Машины ─────────────────────────────────────────────────
        vehicles = [
            Vehicle(plate_number="А123ВС77", brand="ГАЗон Next", length_m=5.1, width_m=2.1,
                    height_m=2.2, volume_cubic_m=23.5, capacity_kg=5000,
                    base_rate_per_km=55, fuel_consumption_per_100km=18.0, fuel_price_per_liter=58.0,
                    status=VehicleStatus.available),
            Vehicle(plate_number="М456КТ77", brand="MAN TGS 26.440", length_m=7.2, width_m=2.45,
                    height_m=2.6, volume_cubic_m=45.9, capacity_kg=12000,
                    base_rate_per_km=82, fuel_consumption_per_100km=28.0, fuel_price_per_liter=60.0,
                    status=VehicleStatus.available),
            Vehicle(plate_number="О789РА77", brand="Volvo FH 500", length_m=13.6, width_m=2.45,
                    height_m=2.7, volume_cubic_m=90.0, capacity_kg=22000,
                    base_rate_per_km=118, fuel_consumption_per_100km=35.0, fuel_price_per_liter=60.0,
                    status=VehicleStatus.in_trip),
            Vehicle(plate_number="Е321КМ16", brand="Scania R450", length_m=13.6, width_m=2.45,
                    height_m=2.7, volume_cubic_m=88.0, capacity_kg=20000,
                    base_rate_per_km=112, fuel_consumption_per_100km=33.0, fuel_price_per_liter=60.0,
                    status=VehicleStatus.available),
            Vehicle(plate_number="У099НО23", brand="Mercedes Actros 1853", length_m=13.6, width_m=2.45,
                    height_m=2.75, volume_cubic_m=92.0, capacity_kg=24000,
                    base_rate_per_km=125, fuel_consumption_per_100km=36.0, fuel_price_per_liter=62.0,
                    status=VehicleStatus.maintenance),
        ]
        db.add_all(vehicles)
        db.flush()

        # ── Водители ───────────────────────────────────────────────
        drivers = [
            Driver(full_name="Иван Петров", license_category="C, E", experience_years=9,
                   assigned_vehicle_id=vehicles[0].id, status=DriverStatus.available),
            Driver(full_name="Сергей Волков", license_category="C, E", experience_years=14,
                   assigned_vehicle_id=vehicles[1].id, status=DriverStatus.available),
            Driver(full_name="Андрей Соколов", license_category="C, E", experience_years=11,
                   assigned_vehicle_id=vehicles[2].id, status=DriverStatus.in_trip),
            Driver(full_name="Дмитрий Кузнецов", license_category="C, E", experience_years=7,
                   assigned_vehicle_id=vehicles[3].id, status=DriverStatus.available),
            Driver(full_name="Алексей Новиков", license_category="C, E", experience_years=20,
                   assigned_vehicle_id=vehicles[4].id, status=DriverStatus.rest),
            Driver(full_name="Михаил Зайцев", license_category="C", experience_years=4,
                   assigned_vehicle_id=None, status=DriverStatus.available),
        ]
        db.add_all(drivers)
        db.flush()

        # ── Клиенты ────────────────────────────────────────────────
        clients = [
            Client(name="ООО СеверЛогистик", contacts="+7 900 100-20-30, order@sever.ru"),
            Client(name="ИП Каримов Б.Т.", contacts="+7 701 111-22-33"),
            Client(name="ТОО АлматыТрейд", contacts="+7 700 555-66-77, trade@almaty.kz"),
            Client(name="ЗАО МеталлПром", contacts="+7 495 300-40-50, metal@prom.ru"),
            Client(name="ООО ПластГрупп", contacts="+7 812 600-70-80, info@plastgrupp.ru"),
            Client(name="ИП Назаров А.Р.", contacts="+7 905 222-33-44"),
        ]
        db.add_all(clients)
        db.flush()

        # ── Заявки на перевозку (CargoRequest) ───────────────────
        requests_data = [
            # (client, cargo_name, features, weight_kg, volume, origin, dest)
            (clients[0], "Стальные трубы", "Металл, тяжёлое", 18000, 62.0, "Москва, склад №3", "Екатеринбург, завод", -33),
            (clients[1], "Бытовая техника", "Хрупкое, срочное", 4200, 20.0, "Алматы, ТЦ Мега", "Нур-Султан, ул. Абая 5", -55),
            (clients[2], "Продукты питания", "Скоропорт, охлаждение", 8500, 42.0, "Алматы, рынок Алтын", "Шымкент, ул. Рыскулова", -40),
            (clients[3], "Листовой металл", "Металл, длинномер", 20000, 80.0, "Магнитогорск, ММК", "Казань, завод КамАЗ", -60),
            (clients[4], "Пластиковые гранулы", "Сыпучий груз", 12000, 55.0, "Уфа, химзавод", "Самара, склад", -20),
            (clients[5], "Мебель", "Хрупкое, объёмное", 3500, 38.0, "Москва, ТЦ ИКЕА", "Воронеж, мебельный центр", -10),
            (clients[0], "Строительные материалы", "Сыпучее", 10000, 48.0, "Санкт-Петербург", "Москва, стройка", 0),
            (clients[2], "Запчасти для авто", "Металл", 6000, 28.0, "Ташкент, завод", "Алматы, авторынок", 0),
        ]

        cargo_requests = []
        for i, (client, cargo_name, features, weight, vol, origin, dest, days_ago) in enumerate(requests_data):
            cr = CargoRequest(
                client_id=client.id,
                cargo_name=cargo_name,
                cargo_features=features,
                weight_kg=weight,
                volume_cubic_m=vol,
                origin=origin,
                destination=dest,
                created_at=date.today() + timedelta(days=days_ago),
            )
            db.add(cr)
            cargo_requests.append(cr)
        db.flush()

        # ── Рейсы (Orders) ────────────────────────────────────────
        def make_order(cr, vehicle, driver, dist_km, other_costs, status, dep_days, del_days=None):
            final_price = round(dist_km * vehicle.base_rate_per_km, 2)
            fuel_cost = round(dist_km * vehicle.fuel_consumption_per_100km / 100 * vehicle.fuel_price_per_liter, 2)
            other = round(other_costs, 2)
            profit = round(final_price - fuel_cost - other, 2)
            dep_date = date.today() + timedelta(days=dep_days) if dep_days is not None else None
            del_date = date.today() + timedelta(days=del_days) if del_days is not None else None
            return Order(
                cargo_request_id=cr.id,
                vehicle_id=vehicle.id,
                driver_id=driver.id,
                distance_km=dist_km,
                final_price=final_price,
                fuel_cost=fuel_cost,
                other_costs=other,
                profit=profit,
                status=status,
                departure_date=dep_date,
                delivery_date=del_date,
            )

        orders = [
            # Завершённые рейсы
            make_order(cargo_requests[0], vehicles[2], drivers[2], 1850, 8500, OrderStatus.delivered, -33, -30),
            make_order(cargo_requests[1], vehicles[0], drivers[0], 1200, 3200, OrderStatus.delivered, -55, -53),
            make_order(cargo_requests[2], vehicles[1], drivers[1], 680,  4100, OrderStatus.delivered, -40, -39),
            make_order(cargo_requests[3], vehicles[2], drivers[2], 1420, 6200, OrderStatus.delivered, -60, -57),
            make_order(cargo_requests[4], vehicles[3], drivers[3], 420,  2800, OrderStatus.delivered, -20, -19),
            make_order(cargo_requests[5], vehicles[0], drivers[0], 510,  3100, OrderStatus.delivered, -10, -9),
            # В пути
            make_order(cargo_requests[6], vehicles[2], drivers[2], 710,  4500, OrderStatus.in_transit, -2),
            # Назначен
            make_order(cargo_requests[7], vehicles[1], drivers[1], 3200, 9800, OrderStatus.assigned, 1),
        ]
        db.add_all(orders)

        # Обновим статусы машин и водителей по активным рейсам
        vehicles[2].status = VehicleStatus.in_trip
        drivers[2].status = DriverStatus.in_trip
        vehicles[1].status = VehicleStatus.in_trip
        drivers[1].status = DriverStatus.in_trip

        db.commit()
        total_income = sum(o.final_price for o in orders)
        total_fuel = sum(o.fuel_cost for o in orders)
        total_profit = sum(o.profit for o in orders)
        print("Demo data loaded successfully!")
        print(f"  Vehicles: {len(vehicles)}")
        print(f"  Drivers:  {len(drivers)}")
        print(f"  Clients:  {len(clients)}")
        print(f"  Requests: {len(cargo_requests)}")
        print(f"  Orders:   {len(orders)}")
        print(f"\n  Total income:  {total_income:,.0f}")
        print(f"  Fuel costs:    {total_fuel:,.0f}")
        print(f"  Net profit:    {total_profit:,.0f}")


if __name__ == "__main__":
    run()
