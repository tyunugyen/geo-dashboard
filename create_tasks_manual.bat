@echo off
echo Creating GEO Dashboard Scheduled Tasks...

schtasks /create /tn "GEO Weekly Benchmark" /tr "C:\Users\tyunguyen\geo-dashboard\geo_weekly_benchmark.bat" /sc weekly /d MON /st 09:00 /f

schtasks /create /tn "GEO Fill Session (Weekly)" /tr "C:\Users\tyunguyen\geo-dashboard\geo_fill_session.bat" /sc weekly /d MON /st 10:00 /f

schtasks /create /tn "GEO Monthly Benchmark" /tr "C:\Users\tyunguyen\geo-dashboard\geo_monthly_benchmark.bat" /sc weekly /d MON /st 11:00 /f

schtasks /create /tn "GEO Fill Session (Monthly)" /tr "C:\Users\tyunguyen\geo-dashboard\geo_fill_session.bat" /sc weekly /d MON /st 12:30 /f

echo.
echo Done! Tasks created:
schtasks /query /tn "GEO*"
