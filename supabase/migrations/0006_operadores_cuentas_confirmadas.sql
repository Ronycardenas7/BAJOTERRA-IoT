-- Registra como operadores a las cuentas de correo confirmadas.
-- La asignación ocurre en la base de datos; el navegador no escribe en operadores.
create or replace function privado.asignar_operador_confirmado()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  -- Aplica tanto a registros nuevos como a confirmaciones posteriores.
  insert into public.operadores (usuario)
  values (new.id)
  on conflict (usuario) do nothing;
  return new;
end;
$$;

-- Solo el disparador de Auth debe ejecutar esta función.
revoke all on function privado.asignar_operador_confirmado() from public, anon, authenticated;

-- La confirmación desde correo habilita el control sin intervención manual.
create or replace trigger asignar_operador_confirmado
after insert or update of email_confirmed_at, is_anonymous on auth.users
for each row
when (new.email_confirmed_at is not null and not new.is_anonymous)
execute function privado.asignar_operador_confirmado();

-- Asigna también el permiso a las cuentas confirmadas que ya existen.
insert into public.operadores (usuario)
select id from auth.users
where email_confirmed_at is not null and not is_anonymous
on conflict (usuario) do nothing;
