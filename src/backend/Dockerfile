FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# WeasyPrint (FR-10/FR-14) cần pango/cairo ở mức hệ thống; fonts-dejavu để
# render được dấu tiếng Việt trong hợp đồng và hóa đơn. curl dùng cho healthcheck.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        fonts-dejavu-core \
        libcairo2 \
        libfontconfig1 \
        libgdk-pixbuf-2.0-0 \
        libharfbuzz0b \
        libpango-1.0-0 \
        libpangoft2-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# INSTALL_DEV=true cho môi trường dev/CI để có pytest, ruff, mypy trong container.
ARG INSTALL_DEV=false

COPY requirements.txt requirements-dev.txt ./
RUN if [ "$INSTALL_DEV" = "true" ]; then \
        pip install -r requirements-dev.txt; \
    else \
        pip install -r requirements.txt; \
    fi

COPY . .

# Thư mục kho tệp riêng tư; compose mount volume vào đây.
RUN mkdir -p /var/lib/rem/files

EXPOSE 8000

# Không đặt --reload trong image. Compose dev thêm --reload qua command.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
