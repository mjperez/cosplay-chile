import { Modulos } from '../components/home/Modulos'
import { Pasos } from '../components/home/Pasos'
import { Portada } from '../components/home/Portada'
import { Disposicion } from '../components/layout/Disposicion'

export function InicioPagina() {
  return (
    <Disposicion>
      <Portada />
      <Modulos />
      <Pasos />
    </Disposicion>
  )
}
