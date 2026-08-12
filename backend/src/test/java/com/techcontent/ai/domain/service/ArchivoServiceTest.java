package com.techcontent.ai.domain.service;

import com.techcontent.ai.api.dto.response.ArchivoResponse;
import com.techcontent.ai.api.exception.ArchivoNotFoundException;
import com.techcontent.ai.domain.model.Archivo;
import com.techcontent.ai.domain.repository.ArchivoRepository;
import com.techcontent.ai.integration.oci.OciStorageClient;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.util.ReflectionTestUtils;

import java.io.IOException;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class ArchivoServiceTest {

    @Mock
    private ArchivoRepository archivoRepository;

    @Mock
    private OciStorageClient ociStorageClient;

    @InjectMocks
    private ArchivoService archivoService;

    private UUID userId;

    @BeforeEach
    void setUp() {
        userId = UUID.randomUUID();

        // El campo filesBucket se inyecta con @Value en la clase real, algo
        // que Spring hace solo cuando levanta el contexto completo. Como acá
        // NO levantamos Spring (es un test unitario puro, más rápido),
        // tenemos que setearlo a mano con ReflectionTestUtils.
        ReflectionTestUtils.setField(archivoService, "filesBucket", "techcontent-files-test");
    }

    @Test
    void subir_archivoValido_deberiaSubirYGuardar() throws IOException {
        // ARRANGE
        // MockMultipartFile es una clase de Spring hecha justamente para
        // testing: simula un archivo subido por HTTP sin necesitar un
        // request real.
        MockMultipartFile file = new MockMultipartFile(
                "file",                    // nombre del parametro
                "documento.pdf",            // nombre original del archivo
                "application/pdf",          // content type
                "contenido de prueba".getBytes()
        );

        when(ociStorageClient.upload(anyString(),anyString(),any(),anyLong(),anyString() )).thenReturn("https://storage.example.com/documento.pdf");

        when(archivoRepository.save(any(Archivo.class))).thenAnswer(invocation -> {
            Archivo a = invocation.getArgument(0);
            a.setId(UUID.randomUUID());
            return a;
        });

        // ACT
        ArchivoResponse response = archivoService.subir(file, userId);

        // ASSERT
        assertNotNull(response);
        assertEquals("documento.pdf", response.nombre());
        assertEquals("https://storage.example.com/documento.pdf", response.url());
        assertEquals("application/pdf", response.tipo());

        verify(ociStorageClient, times(1)).upload( eq("techcontent-files-test"),anyString(),any(),eq(file.getSize()),eq("application/pdf"));
        verify(archivoRepository, times(1)).save(any(Archivo.class));
    }

    @Test
    void subir_archivoVacio_deberiaLanzarIllegalArgumentException() {
        // Caso borde: archivo sin contenido. La validacion tiene que
        // rechazarlo ANTES de intentar subirlo a OCI.
        MockMultipartFile fileVacio = new MockMultipartFile(
                "file", "vacio.pdf", "application/pdf", new byte[0]
        );

        IllegalArgumentException ex = assertThrows(
                IllegalArgumentException.class,
                () -> archivoService.subir(fileVacio, userId)
        );

        assertEquals("El archivo no puede estar vacio", ex.getMessage());

        // Verificamos que, al fallar la validacion, NUNCA se haya intentado
        // subir el archivo ni guardarlo. Esto es tan importante como el
        // mensaje de error: confirma que el metodo corta la ejecucion a tiempo.
        verifyNoInteractions(ociStorageClient);
        verifyNoInteractions(archivoRepository);
    }

    @Test
    void subir_tipoNoPermitido_deberiaLanzarIllegalArgumentException() {
        MockMultipartFile fileInvalido = new MockMultipartFile(
                "file", "imagen.png", "image/png", "contenido".getBytes()
        );

        IllegalArgumentException ex = assertThrows(
                IllegalArgumentException.class,
                () -> archivoService.subir(fileInvalido, userId)
        );

        assertTrue(ex.getMessage().contains("Tipo de archivo no permitido"));
        verifyNoInteractions(ociStorageClient);
    }

    @Test
    void subir_archivoSuperaTamanoMaximo_deberiaLanzarIllegalArgumentException() {
        // Simulamos un archivo de 11 MB (el limite real del Service es 10 MB).
        // No hace falta generar 11 MB de datos reales: MockMultipartFile
        // permite pasar contenido chico y el Service igual valida por el
        // tamano que reporta file.getSize(), así que alcanza con un contenido
        // cuyo length en bytes sea el que queremos simular.
        byte[] contenidoGrande = new byte[11 * 1024 * 1024];
        MockMultipartFile fileGrande = new MockMultipartFile(
                "file", "grande.pdf", "application/pdf", contenidoGrande
        );

        IllegalArgumentException ex = assertThrows(
                IllegalArgumentException.class,
                () -> archivoService.subir(fileGrande, userId)
        );

        assertTrue(ex.getMessage().contains("tamano maximo"));
        verifyNoInteractions(ociStorageClient);
    }

    @Test
    void listar_deberiaDevolverArchivosDelUsuario() {
        Archivo archivo = Archivo.builder()
                .id(UUID.randomUUID())
                .userId(userId)
                .nombre("mi-archivo.pdf")
                .url("https://storage.example.com/mi-archivo.pdf")
                .tamano(1024L)
                .tipo("application/pdf")
                .subidoEn(LocalDateTime.now())
                .build();

        when(archivoRepository.findByUserId(userId)).thenReturn(List.of(archivo));

        List<ArchivoResponse> resultados = archivoService.listar(userId);

        assertEquals(1, resultados.size());
        assertEquals("mi-archivo.pdf", resultados.get(0).nombre());
        verify(archivoRepository, times(1)).findByUserId(userId);
    }

    @Test
    void obtenerPorId_archivoExiste_deberiaDevolverlo() {
        UUID archivoId = UUID.randomUUID();
        Archivo archivo = Archivo.builder()
                .id(archivoId)
                .userId(userId)
                .nombre("encontrado.pdf")
                .url("https://storage.example.com/encontrado.pdf")
                .tamano(2048L)
                .tipo("application/pdf")
                .subidoEn(LocalDateTime.now())
                .build();

        when(archivoRepository.findByIdAndUserId(archivoId, userId)).thenReturn(Optional.of(archivo));

        ArchivoResponse response = archivoService.obtenerPorId(archivoId, userId);

        assertEquals("encontrado.pdf", response.nombre());
    }

    @Test
    void obtenerPorId_archivoNoExiste_deberiaLanzarArchivoNotFoundException() {
        // Caso importante: cuando el repo devuelve Optional.empty(), el
        // Service tiene que transformarlo en una excepcion de negocio
        // (ArchivoNotFoundException), no dejar pasar un null ni explotar
        // con NoSuchElementException generico.
        UUID archivoIdInexistente = UUID.randomUUID();
        when(archivoRepository.findByIdAndUserId(archivoIdInexistente, userId))
                .thenReturn(Optional.empty());

        assertThrows(
                ArchivoNotFoundException.class,
                () -> archivoService.obtenerPorId(archivoIdInexistente, userId)
        );
    }
}